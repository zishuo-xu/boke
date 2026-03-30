from app.application.chat.services import ProviderRegistry
from app.domain.chat.entities import ProviderType
from app.infrastructure.providers.anthropic_gateway import AnthropicGateway
from app.infrastructure.providers.openai_gateway import OpenAICompatibleGateway


def build_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(
        {
            ProviderType.OPENAI_COMPATIBLE: OpenAICompatibleGateway(),
            ProviderType.ANTHROPIC: AnthropicGateway(),
        }
    )
