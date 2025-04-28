from django.views.generic import TemplateView
from mailing.forms import SampleEmailForm


class HomeTemplateView(TemplateView):
    template_name = 'common/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sample_form'] = SampleEmailForm()
        return context
