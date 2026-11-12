
from __future__ import annotations

from django.shortcuts import redirect
from django.views.generic import CreateView, UpdateView

from .processor import ModelFormProcessor


class InlineFormViewMixin:
    
    processor_class = ModelFormProcessor

    def get_processor(self, *, data=None, files=None):
        return self.processor_class(
            self.get_form_class(),
            data=data,
            files=files,
            instance=self.object,
            prefix=self.get_prefix(),
        )

    def get_context_data(self, **kwargs):
        processor = kwargs.pop("processor", None)

        if processor is None:
            processor = self.get_processor()

        context = super().get_context_data(
            form=processor.form,
            **kwargs,
        )

        context["processor"] = processor
        context["form"] = processor.form
        context["formsets"] = processor.formsets

        return context

    def render_processor(self, processor):
        return self.render_to_response(
            self.get_context_data(processor=processor)
        )

    def process_post(self):
        processor = self.get_processor(
            data=self.request.POST,
            files=self.request.FILES,
        )

        if not processor.is_valid():
            return self.render_processor(processor)

        self.object = processor.save()

        return redirect(self.get_success_url())


class InlineCreateView(InlineFormViewMixin, CreateView):
    """
    Create a parent object together with its inline objects.
    """

    def get(self, request, *args, **kwargs):
        self.object = None
        return self.render_processor(self.get_processor())

    def post(self, request, *args, **kwargs):
        self.object = None
        return self.process_post()


class InlineUpdateView(InlineFormViewMixin, UpdateView):
    """
    Update a parent object together with its inline objects.
    """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_processor(self.get_processor())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.process_post()
