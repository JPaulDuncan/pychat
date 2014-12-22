# -*- encoding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as djangologin
from django.contrib.auth import logout as djangologout
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from story.models import UserProfile
from .models import Messages
import random
from django.http import Http404
import string
from drealtime import iShoutClient
import registration_utils


def validate_email(request):
	email = request.POST['email']
	response = registration_utils.validate_email(email)
	return HttpResponse(response, content_type='text/plain')

def validate_user(request):
	username = request.POST['username']
	response = registration_utils.validate_user(username)
	return HttpResponse(response, content_type='text/plain')


def shout(request):
	ishout_client = iShoutClient()
	ishout_client.broadcast(
		channel='notifications',
		data={'data': 'it works'})


def repr_dict(d):
	return '{%s}' % ', '.join("'%s': '%s'" % pair for pair in d.items())


def home(request):
	c = {}
	c.update(csrf(request))
	if request.user.is_authenticated():
		if request.method == 'POST':
			content = request.POST.get('message', '')
			message = Messages(userid=request.user, content=content)
			message.save()
			ishout_client = iShoutClient()
			ishout_client.broadcast(
				channel='notifications',
				data={
					'user': request.user.username,
					'content': message.content,
					'hour': message.time.hour,
					'minute': message.time.minute}
			)
			message = 'message delivered'
			return HttpResponse(message, content_type='text/plain')
		else:
			messages = Messages.objects.all().order_by('pk').reverse()[:20]
			passed_messages = []
			for singleMess in reversed(messages):
				messages = {
					'hour': singleMess.time.hour,
					'minute': singleMess.time.minute,
					'content': singleMess.content,
					'user': User.objects.get_by_natural_key(singleMess.userid).username}
				passed_messages.append(repr_dict(messages))
			page = 'story/logout.html'
			my_list = {'username': request.user.username, 'messages': passed_messages}
			c.update(my_list)
	else:
		page = 'story/login.html'
	return render_to_response(page, c)


def logout(request):
	djangologout(request)
	return home(request)


def auth(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if user is not None:
		djangologin(request, user)
		message = "update"
	else:
		message = "Login or password is wrong"
	return HttpResponse(message, content_type='text/plain')


def confirm_email(request):
	if request.method == 'GET':
		code = request.GET.get('code', False)
		try:
			u = UserProfile.objects.get(verify_code=code)
			if u.email_verified is False:
				u.email_verified = True
				u.save()
				message = 'verification code is accepted'
			else:
				message = 'This code is already accepted'
		except UserProfile.DoesNotExist:
			raise Http404
	else:
		message = "invalid request"
	return render_to_response("story/confirm_mail.html", {'message': message})


def register(request):
	if request.is_ajax():
		registration_result = registration_utils.register_user(
			request.POST['username'],
			request.POST['password'],
			request.POST['email'],
			request.POST.get('mailbox', False)
		)
		if registration_result['message'] is False:
			djangologin(request, registration_result['user'])
			# register,js redirect if message = 'Account created'
			registration_result['message'] = 'Account created'
		return HttpResponse(registration_result['message'], content_type='text/plain')
	else:
		c = {}
		mycrsf = csrf(request)
		c.update(mycrsf)
		c.update({'error code': "welcome to register page"})
		return render_to_response("story/register.html", c)