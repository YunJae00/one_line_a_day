from django.shortcuts import render
from django.views.generic import TemplateView
from mailing.forms import SampleEmailForm, TrialSubscriptionForm
from subscriptions.forms import DirectSubscriptionForm


class HomeTemplateView(TemplateView):
    template_name = 'common/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sample_form'] = SampleEmailForm()
        # context['trial_form'] = TrialSubscriptionForm()
        context['subscription_form'] = DirectSubscriptionForm()
        return context


def handler404(request, exception):
    """
    커스텀 404 에러 핸들러
    """
    context = {
        'requested_url': request.path,
    }
    return render(request, 'common/404.html', context, status=404)