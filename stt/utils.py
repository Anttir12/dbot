import calendar
from datetime import datetime
from azure.mgmt.monitor import MonitorManagementClient
from azure.identity import ClientSecretCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from dbot import settings


def get_speech_synthesis_usage_chars():
    monitor_mgmt_client, speech_service = _create_mgmt_client_and_speech_service()
    start_time, end_time = _get_month_range()
    metrics_data = monitor_mgmt_client.metrics.list(
        speech_service.id,
        timespan=f"{start_time}/{end_time}",
        metricnames="SynthesizedCharacters",
        result_type="Total"
    )

    # Calculate the total number of seconds transcribed
    characters = 0

    if metrics_data.value:
        for item in metrics_data.value[0].timeseries:
            for data_point in item.data:
                characters += data_point.total

    return characters


def get_speech_recognition_usage_seconds():
    monitor_mgmt_client, speech_service = _create_mgmt_client_and_speech_service()
    start_time, end_time = _get_month_range()
    metrics_data = monitor_mgmt_client.metrics.list(
        speech_service.id,
        timespan=f"{start_time}/{end_time}",
        metricnames="AudioSecondsTranscribed",
        result_type="Total"
    )

    # Calculate the total number of seconds transcribed
    seconds_transcribed = 0

    if metrics_data.value:
        for item in metrics_data.value[0].timeseries:
            for data_point in item.data:
                seconds_transcribed += data_point.total

    return seconds_transcribed


def _get_month_range():
    now = datetime.utcnow()
    start_time = datetime(now.year, now.month, 1)
    last_day = calendar.monthrange(now.year, now.month)[1]
    end_time = datetime(now.year, now.month, last_day)

    start_time_str = start_time.strftime('%Y-%m-%dT%H:%MZ')
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%MZ')

    return start_time_str, end_time_str


def _create_mgmt_client_and_speech_service():
    client_id = settings.AZURE_CLIENT_ID
    client_secret = settings.AZURE_CLIENT_SECRET
    tenant_id = settings.AZURE_TENANT_ID

    # Replace 'your_subscription_id' with your own Azure subscription ID
    subscription_id = settings.AZURE_SUBSCRIPTION_ID

    resource_group_name = settings.AZURE_RESOURCE_GROUP
    cognitive_services_account_name = settings.AZURE_SERVICE_ACCOUNT_NAME

    credentials = ClientSecretCredential(tenant_id, client_id, client_secret)

    # Create a MonitorManagementClient object.
    monitor_mgmt_client = MonitorManagementClient(credentials, subscription_id)

    cognitive_services_mgmt_client = CognitiveServicesManagementClient(credentials, subscription_id)
    speech_service = cognitive_services_mgmt_client.accounts.get(resource_group_name, cognitive_services_account_name)

    return monitor_mgmt_client, speech_service
