from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from django.http import HttpRequest

from djangospice.response.response import Response

T_Rendered = TypeVar("T_Rendered")
T_Content = TypeVar("T_Content")


class BaseRenderer(ABC, Generic[T_Rendered, T_Content]):
    """
        Base renderer definitions and rendering pipeline architecture.

        This module defines the abstract interface for transforming transport-agnostic
        djangospice Responses into transport-specific outputs (HTML, JSON, HTMX, etc.).
    """

    name: str
    priority: int = 100

    @abstractmethod
    def supports(self, request: HttpRequest | None) -> bool:
        """
        Return whether this renderer supports the incoming request.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(self, response: Response) -> Response:
        """
        Prepare or mutate the response state before rendering begins.
        """
        return response

    @abstractmethod
    def build_content(self, response: Response) -> T_Content:
        """
        Produce the renderer-specific content representation.
        """
        raise NotImplementedError

    @abstractmethod
    def build_response(self, response: Response, content: T_Content) -> T_Rendered:
        """
        Wrap the generated content into the final transport response type.
        """
        raise NotImplementedError

    def finalize_response(self, response: Response, rendered: T_Rendered) -> T_Rendered:
        """
        Final lifecycle hook before returning the rendered response.
        """
        return rendered

    # ------------------------------------------------------------------
    # Rendering Hook
    # ------------------------------------------------------------------

    def render(self, response: Response) -> T_Rendered:
        """
        Execute the complete rendering pipeline.
        """
        response = self.prepare(response)
        
        content = self.build_content(response)
        
        rendered = self.build_response(
            response=response,
            content=content,
        )
        
        return self.finalize_response(
            response=response,
            rendered=rendered,
        )