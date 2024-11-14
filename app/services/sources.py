from app.api.dependencies import get_config, get_sources_repo


class SourcesService:
    def __init__(self):
        self.config = get_config()
        self.source_repo = get_sources_repo()


