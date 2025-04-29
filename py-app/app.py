import logging.config
import logging.config
import os
import time
import uuid

from cltl.chatui.api import Chats
from cltl.chatui.memory import MemoryChats
from cltl.combot.event.emissor import Agent, ScenarioStarted, ScenarioStopped
from cltl.combot.infra.config.k8config import K8LocalConfigurationContainer
from cltl.combot.infra.di_container import singleton
from cltl.combot.infra.event import Event
from cltl.combot.infra.event.memory import SynchronousEventBusContainer
from cltl.combot.infra.event_log import LogWriter
from cltl.combot.infra.resource.threaded import ThreadedResourceContainer
from cltl.combot.infra.time_util import timestamp_now
from cltl.emissordata.api import EmissorDataStorage
from cltl.emissordata.file_storage import EmissorDataFileStorage
from cltl.llm.api import LLM
from cltl.llm.llm import LLMImpl

from cltl_service.chatui.service import ChatUiService
from cltl_service.combot.event_log.service import EventLogService
from emissor.representation.scenario import Modality, Scenario, ScenarioContext
from cltl_service.emissordata.client import EmissorDataClient
from cltl_service.emissordata.service import EmissorDataService
from cltl_service.llm.service import LLMService

from emissor.representation.util import serializer as emissor_serializer
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from emissor.representation.ldschema import emissor_dataclass
import json

logging.config.fileConfig(os.environ.get('CLTL_LOGGING_CONFIG', default='config/logging.config'),
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class InfraContainer(SynchronousEventBusContainer, K8LocalConfigurationContainer, ThreadedResourceContainer):
    pass


class EmissorStorageContainer(InfraContainer):
    @property
    @singleton
    def emissor_storage(self) -> EmissorDataStorage:
        return EmissorDataFileStorage.from_config(self.config_manager)

    @property
    @singleton
    def emissor_data_service(self) -> EmissorDataService:
        return EmissorDataService.from_config(self.emissor_storage,
                                              self.event_bus, self.resource_manager, self.config_manager)

    @property
    @singleton
    def emissor_data_client(self) -> EmissorDataClient:
        return EmissorDataClient("http://0.0.0.0:8000/emissor")

    def start(self):
        logger.info("Start Emissor Data Storage")
        super().start()
        self.emissor_data_service.start()

    def stop(self):
        try:
            logger.info("Stop Emissor Data Storage")
            self.emissor_data_service.stop()
        finally:
            super().stop()


class ChatUIContainer(InfraContainer):
    @property
    @singleton
    def chats(self) -> Chats:
        return MemoryChats()

    @property
    @singleton
    def chatui_service(self) -> ChatUiService:
        return ChatUiService.from_config(MemoryChats(), self.event_bus, self.resource_manager, self.config_manager)

    def start(self):
        logger.info("Start Chat UI")
        super().start()
        self.chatui_service.start()

    def stop(self):
        try:
            logger.info("Stop Chat UI")
            self.chatui_service.stop()
        finally:
            super().stop()




class LLMContainer(EmissorStorageContainer, InfraContainer):
    @property
    @singleton
    def llm(self) -> LLM:


        config = self.config_manager.get_config("cltl.llm")

        model = config.get("model") if "model" in config else None
        instruction_content = config.get("instruction") if "instruction" in config else None
        instruction ={"role": "system", "content": instruction_content}
        temperature = config.get("temperature") if "temperature" in config else None
        port = config.get("port") if "port" in config else None
        max_history = config.get("max_history") if "max_history" in config else None
        intro = config.get("intro") if "intro" in config else None
        stop = config.get("stop") if "stop" in config else None
        server = False
        if "server" in config:
            server = True
        if not model:
            logger.info("No model specified in de config", config)
            return None
        else:
            return LLMImpl(model_name=model, instruction=instruction,  intro = intro, stop = stop,  temperature=float(temperature), max_history=int(max_history), server=server, port =port)


    @property
    @singleton
    def llm_service(self) -> LLMService:
        return LLMService.from_config(self.llm, self.emissor_data_client,
                                        self.event_bus, self.resource_manager, self.config_manager, self.emissor_storage)

    def start(self):
        logger.info("Start LLM")
        super().start()
        self.llm_service.start()

    def stop(self):
        logger.info("Stop LLM")
        self.llm_service.stop()
        super().stop()

@emissor_dataclass
class ApplicationContext(ScenarioContext):
    speaker: Agent


class ApplicationContainer(LLMContainer, ChatUIContainer, EmissorStorageContainer):
    @property
    @singleton
    def log_writer(self):
        config = self.config_manager.get_config("cltl.event_log")

        return LogWriter(config.get("log_dir"), serializer)

    @property
    @singleton
    def event_log_service(self):
        return EventLogService.from_config(self.log_writer, self.event_bus, self.config_manager)

    def _start_scenario(self):
        scenario_topic = self.config_manager.get_config("cltl.context").get("topic_scenario")
        scenario = self._create_scenario()
        self.event_bus.publish(scenario_topic,
                                Event.for_payload(ScenarioStarted.create(scenario)))
        self._scenario = scenario
        logger.info("Started scenario %s", scenario)

    def _stop_scenario(self):
        scenario_topic = self.config_manager.get_config("cltl.context").get("topic_scenario")
        self._scenario.ruler.end = timestamp_now()
        self.event_bus.publish(scenario_topic,
                                Event.for_payload(ScenarioStopped.create(self._scenario)))
        logger.info("Stopped scenario %s", self._scenario)

    def _create_scenario(self):
        signals = {
            Modality.TEXT.name.lower(): "./text.json",
        }

        scenario_start = timestamp_now()

        agent = Agent("Leolani", "http://cltl.nl/leolani/world/leolani")
        speaker = Agent("Human", "http://cltl.nl/leolani/world/human")
        scenario_context = ApplicationContext(agent, speaker)
        scenario = Scenario.new_instance(str(uuid.uuid4()), scenario_start, None, scenario_context, signals)

        return scenario

    def start(self):
        logger.info("Start EventLog")
        super().start()
        self.event_log_service.start()
        self._start_scenario()


    def stop(self):
        try:
            self._stop_scenario()
            time.sleep(1)
            logger.info("Stop EventLog")
            self.event_log_service.stop()
        finally:
            super().stop()


def serializer(obj):
    try:
        return emissor_serializer(obj)
    except Exception:
        try:
            return vars(obj)
        except Exception:
            return str(obj)


def main():
    ApplicationContainer.load_configuration()
    logger.info("Initialized Application")
    application = ApplicationContainer()

    with application as started_app:
        routes = {
            '/emissor': started_app.emissor_data_service.app,
            '/chatui': started_app.chatui_service.app,
            # ADD ADDITIONAL ENDPOINTS HERE
        }

        web_app = DispatcherMiddleware(Flask("Demo app"), routes)

        run_simple('0.0.0.0', 8000, web_app, threaded=True, use_reloader=False, use_debugger=False, use_evalex=True)


if __name__ == '__main__':
    main()
