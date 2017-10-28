from datetime import datetime
# requires Twilio

"""
		This script will read the latest spaceweather data from a NOAA feed
		and notify via text when parameters reach a certain threshold. This
		is effectively an aurora alert service.
"""


class Spaceweather:

	def __init__(self):
		self.urls = [
			'http://services.swpc.noaa.gov/text/ace-swepam.txt',
			'http://services.swpc.noaa.gov/text/ace-magnetometer.txt'
		]
		# solar wind data
		self.proton_density = []
		self.solar_wind_speed = []
		self.solar_wind_temp = []
		# magnetosphere data
		self.bx = []
		self.by = []
		self.bz = []
		self.bt = []

		self.request_data()


	def current_reading(self,param):
		return param[len(param)-1]


	def current_conditions(self):

		conditions = """\n
			Solar Wind Speed: {sw} km / s
			Solar Wind Density: {sd}
			Bz: {bz}
			Bt: {bt}
		""".format(
				sw = self.current_reading(self.solar_wind_speed), 
				sd = self.current_reading(self.proton_density),
				bz = self.current_reading(self.bz),
				bt = self.current_reading(self.bt)
		)

		return conditions


	def request_data(self):
		import requests
		import csv

		for url in self.urls:
			request = requests.get(url)
			data = request.text
			reader = csv.reader(data.splitlines(), delimiter='\t')
			for row in reader:
				cols = [x for x in row[0].split(' ') if not x == '']
				if not cols[0][0] in ["#",":"]: # data begins
					time = cols[3]
					if int(cols[6]) < 1: # don't collect bad data
						if "swe" in url:
							# do stuff for solar wind
							self.proton_density.append(cols[7])
							self.solar_wind_speed.append(cols[8])
							self.solar_wind_temp.append(cols[9])
						else:
							# do stuff for magentometer
							self.bx.append(cols[7])
							self.by.append(cols[8])
							self.bz.append(cols[9])
							self.bt.append(cols[10])



class Alert:

	def __init__(self,params):
		self.params = params.strip().split(',')
		self.phone = self.params[0]
		self.bz_threshold = self.params[1]
		self.flare_threshold = self.params[2]
		fmt = '%Y-%m-%d %H%M'
		self.last_bz_alert = datetime.strptime(self.params[3],fmt)

		#self.last_flare_alert = datetime(self.params[4],fmt)



class UserAlerts:

	def __init__(self):
		# phone, minimum bz value, minimum flare value, last alert bz, last alert flare
		self.filename = "registered_alerts.txt"
    self.alert_recurrence = 5 # 1 alert per hours
		self.alerts = []
		with open(self.filename) as alerts:
			for params in alerts:
				self.alerts.append(Alert(params))


	def send(self,spacew_data):

		for alert in self.alerts:
			message = self.alert_needed(alert,spacew_data)
			if message:
				TextMessage(alert.phone, message)
				

	def alert_needed(self, alert, spacew_data):

		# need to add code for flare alerts

		if alert.bz_threshold > spacew_data.current_reading(spacew_data.bz):
			if alert.last_bz_alert:
				time_format = '%Y-%m-%d %H%M'
				current_time = datetime.utcnow()
				tdelta = current_time - alert.last_bz_alert
				if (tdelta.seconds / 3600) > self.alert_recurrence: # more than 5 hours ago
					return spacew_data.current_conditions()
		return False






class TextMessage:

	def __init__(self,number,message):

		from twilio.rest import TwilioRestClient

		accountSID = ''
		accountToken = ''
		twilio_number = ''
		number = "+1{}".format(number)

		twilio_client = TwilioRestClient(accountSID, accountToken)
		twilio_client.messages.create(body=message,from_=twilio_number,to=number)



def main():
	spacew = Spaceweather()
	alerts = UserAlerts()
	alerts.send(spacew)


			
if __name__ == '__main__':
	main()
