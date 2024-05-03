import unittest
from main import app

class FlaskTestCase(unittest.TestCase):
    
    def test_tank_forecast_endpoint(self):
        tester = app.test_client(self)
        response = tester.get('/tank_forecast', content_type='application/json')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(data) > 0)

    def test_sample_endpoint(self):
        tester = app.test_client(self)
        response = tester.post('/tank_forecast_with_dates', json={'start_date': '01-01-2024', 'end_date': '31-01-2024'})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(data) > 0)

if __name__ == '__main__':
    unittest.main()