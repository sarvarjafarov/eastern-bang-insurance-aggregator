from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from insurance_aggregator.analytics import (
    determine_source_label,
    get_metric_total,
    record_metric,
    record_metric_once,
    track_acquisition,
)
from insurance_aggregator.models import DailyMetric


class AnalyticsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _add_session(self, request):
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_record_metric_accumulates(self):
        record_metric('metric-demo', amount=2)
        record_metric('metric-demo', amount=3)
        metric = DailyMetric.objects.get(metric='metric-demo')
        self.assertEqual(metric.count, 5)

    def test_record_metric_once_only_first_call(self):
        request = self._add_session(self.factory.get('/'))
        first = record_metric_once(request, 'once-only', extras={'extra-metric': 2})
        second = record_metric_once(request, 'once-only', extras={'extra-metric': 2})

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(get_metric_total('once-only'), 1)
        self.assertEqual(get_metric_total('extra-metric'), 2)

    def test_determine_source_label_with_utm_and_search_referer(self):
        request_email = self.factory.get('/', {'utm_medium': 'email'})
        self.assertEqual(determine_source_label(request_email), 'Email')

        request_search = self.factory.get('/')
        request_search.META['HTTP_REFERER'] = 'https://www.google.com/?q=test'
        self.assertEqual(determine_source_label(request_search), 'Organic Search')

    def test_track_acquisition_records_source(self):
        request = self._add_session(self.factory.get('/', {'utm_source': 'student-portal'}))
        track_acquisition(request)

        self.assertEqual(get_metric_total('acquisition'), 1)
        self.assertEqual(get_metric_total('source:Student Portal'), 1)
