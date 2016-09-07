
import json
import hmac, hashlib
import threading
import http, http.server
from halibot import HalModule, Context, Message

def make_issues_report(event, payload):
	title = payload['issue']['title']
	user = payload['sender']['login']
	repo = payload['repository']['full_name']

	if payload['action'] == 'opened':
		return 'New issue "{}" opened by {} in {}.'.format(title, user, repo)

	if payload['action'] == 'reopened':
		return 'Issue "{}" reopened by {} in {}.'.format(title, user, repo)

	if payload['action'] == 'closed':
		return 'Issue "{}" closed by {} in {}.'.format(title, user, repo)

	return None

def make_pr_report(event, payload):
	title = payload['pull_request']['title']
	user = payload['sender']['login']
	repo = payload['repository']['full_name']

	if payload['action'] == 'opened':
		return 'Pull request "{}" opened by {} in {}.'.format(title, user, repo)

	if payload['action'] == 'reopened':
		return 'Pull request "{}" reopened by {} in {}.'.format(title, user, repo)

	if payload['action'] == 'closed':
		merged = '' if payload['pull_request']['merged'] else 'not '
		return 'Pull request "{}" closed and {}merged by {} in {}.'.format(title, merged, user, repo)

	return None

def make_report(event, payload):
	fun = {
		'issues': make_issues_report,
		'pull_request': make_pr_report,
	}.get(event, None)
	
	if fun == None:
		return None

	return fun(event, payload)

class GithubHookHandler(http.server.BaseHTTPRequestHandler):

	def do_POST(self):
		module = self.server.module
		config = module.config

		# filter out non-github events
		if not 'X-Github-Event' in self.headers:
			# Ignore and timeout
			module.log.info('Received something that is not a github event, ignoring.')
			return
	
		length = int(self.headers['Content-Length'])
		data = self.rfile.read(length)

		# Do hmac verification if enabled
		# Enabling recommend so people don't send random garbage to the endpoint
		if 'secret' in config:
			h = hmac.new(config['secret'].encode(), msg=data, digestmod=hashlib.sha1)
			expect = 'sha1=' + h.hexdigest()

			if expect != self.headers['X-Hub-Signature']:
				module.log.warning('HMAC signature mismatch!')
				return

		# TODO read charset from header
		payload = json.loads(data.decode('utf-8'))

		event = self.headers['X-Github-Event']
		action = payload.get('action', None)

		module.log.debug('Received {} {} event.'.format(event, action))
		
		# ignore events we didn't ask for
		events = module.events
		if event in events and action in events[event]:
			report = make_report(event, payload)

			# Ignore events we don't know how to handle
			if report != None:
				cxt = Context(**config['context'])
				msg = Message(body=report, author='halibot', context=cxt)
				module.log.debug('Reporting event to ' + config['context']['whom'])
				module.reply(msg)
			else:
				module.log.warning('Could not form report for "{} {}"'.format(event, action))

		self.send_response(204)
		self.end_headers()

class GithubModule(HalModule):

	def init(self):
		self.events = self.config.get('events', {})

		addr = ('', self.config.get('port', 9000))
		self.server = http.server.HTTPServer(addr, GithubHookHandler)
		self.server.module = self
		self.thread = threading.Thread(target=self.server.serve_forever)
		self.thread.start()

	def shutdown(self):
		self.server.shutdown()
		self.thread.join()

