from app.domain.chat.entities import ChatRequest
from app.domain.chat.exceptions import InvalidChatRequestError


class ChatDomainService:
    def validate_request(self, request: ChatRequest) -> None:
        if not request.messages:
            raise InvalidChatRequestError("messages must not be empty")

        if not request.settings:
            if request.session_id:
                return
            raise InvalidChatRequestError("缺少模型配置。")

        if not request.settings.api_key:
            raise InvalidChatRequestError("请先填写 API Key。")

        if not request.settings.model:
            raise InvalidChatRequestError("请先填写模型名称。")

        if not request.settings.base_url:
            raise InvalidChatRequestError("请先填写 Base URL。")
