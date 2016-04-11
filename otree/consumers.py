from channels import Group
from otree.models import Participant
from otree import common_internal
import sys
import json


if sys.version_info[0] == 2:
    from urlparse import parse_qs
else:
    from urllib.parse import parse_qs


def connect_wait_page(message, params):
    try:
        params = parse_qs(str(message.content['query_string']))

        app_label = params['app_label'][0]
        page_index = int(params['page_index'][0])
        model_name = params['model_name'][0]
        model_pk = int(params['model_pk'][0])
    except Exception as e:
        raise e


    group_name = common_internal.channels_wait_page_group_name(
        app_label, page_index, model_name, model_pk
    )
    group = Group(group_name)
    group.add(message.reply_channel)

    # safeguard (redundant) check, in case the message
    # was sent from the server between page load and web socket connect time

    # fixme: app name or app label?
    models_module = common_internal.get_models_module(app_label)

    GroupOrSubsession = {
        'subsession': getattr(models_module, 'Subsession'),
        'group': getattr(models_module, 'Group')
    }[model_name]

    group_or_subsession = GroupOrSubsession.objects.get(pk=model_pk)

    participants_for_this_page = set(
        p.participant for p in group_or_subsession.player_set.all()
    )

    unvisited = set(
        p for p in participants_for_this_page if
        p._index_in_pages < page_index
    )

    if not unvisited:
        message.reply_channel.send(
            {'text': json.dumps(
                {'status': 'ready'})})


def disconnect_wait_page(message, params):
    try:
        params = parse_qs(str(message.content['query_string']))

        app_label = params['app_label'][0]
        page_index = int(params['page_index'][0])
        model_name = params['model_name'][0]
        model_pk = int(params['model_pk'][0])
    except Exception as e:
        raise e

    group_name = common_internal.channels_wait_page_group_name(
        app_label, page_index, model_name, model_pk
    )
    group = Group(group_name)
    group.add(message.reply_channel)

    group.discard(message.reply_channel)


def connect_auto_advance(message, params):
    try:
        params = parse_qs(str(message.content['query_string']))
        participant_code = params['participant_code'][0]
        page_index = int(params['page_index'][0])
    except Exception as e:
        raise e

    group = Group('auto-advance-{}'.format(participant_code))
    group.add(message.reply_channel)

    # redundant check in case there is a rare race condition
    participant = Participant.objects.get(code=participant_code)
    if participant._index_in_pages > page_index:
        message.reply_channel.send(
            {'text': json.dumps(
                {'new_index_in_pages': participant._index_in_pages})}
        )


def disconnect_auto_advance(message, params):
    try:
        params = parse_qs(str(message.content['query_string']))
        participant_code = params['participant_code'][0]
    except Exception as e:
        raise e


    group = Group('auto-advance-{}'.format(participant_code))
    group.discard(message.reply_channel)


'''
def connect_admin_lobby(message):

    Group('admin_lobby').add(message.)
    ids = ParticipantVisit.objects.all()
    Group('admin_lobby').send(ids)


def connect_participant_lobby(message):

    ParticipantVisit(participant_id).save()
    Group('admin_lobby').send({'participant': participant_id})

def disconnect_participant_lobby(message):

    Group('admin_lobby').send({'participant': participant_id, 'action': 'Leaving'})
    ParticipantVisit(participant_id).delete()
'''

