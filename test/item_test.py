import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
import item

class OrderDataTestCase(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_order_id(self):
        o1 = item.OrderData({'symbol': '123', 'price': 123.4, 'volume': 321})
        self.assertEqual(o1.symbol, '123', 'wrong order symbol')
        self.assertEqual(o1.price, 123.4, 'wrong order price')
        self.assertEqual(o1.volume, 321, 'wrong order volume')
        self.assertEqual(o1.order_id, 1, 'wrong order id 1')
        o2 = item.OrderData({})
        self.assertEqual(o2.order_id, 2, 'wrong order id 2')
        o3 = item.OrderData.get_order(1)
        self.assertEqual(o3.order_id, o1.order_id, 'wrong order got')

if __name__ == '__main__':
    unittest.main()
