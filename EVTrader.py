from PyQt5 import QtWidgets, QtCore, Qt
from PyQt5.QtGui import QIcon, QColor, QPalette
import interface
import qdarkstyle
import resources
import sys
import zmq
import json


class EVmqListener(QtCore.QObject):
    message = QtCore.pyqtSignal(str)
    topic_filter = b'{"exchange":"Gdax","instmt":"BTCUSD"'

    def __init__(self):
        QtCore.QObject.__init__(self)
        port = 6002
        server = '127.0.0.1'
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://" + server + ":%s" % port)
        self.socket.setsockopt(zmq.SUBSCRIBE, self.topic_filter)
        self.running = True
        print("Started Market EvmqListener running on: " + server + " Port: " + str(port))

    def swap_topic_filter(self, new_topic_filter):
        self.socket.setsockopt(zmq.UNSUBSCRIBE, self.topic_filter)
        self.topic_filter = new_topic_filter
        self.socket.setsockopt(zmq.SUBSCRIBE, self.topic_filter)

    def loop(self):
        while self.running:
            string = self.socket.recv_string()
            self.message.emit(string)

class EV(QtWidgets.QMainWindow, interface.Ui_MainWindow):
    last_asks = [0, 0, 0, 0, 0]
    last_bids = [0, 0, 0, 0, 0]
    last_px = 0
    coins_owned = 1.00000000

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.statusBar().hide()
        self.setWindowIcon(QIcon(":/icons/colored_cube.png"))

        self.thread = QtCore.QThread()
        self.EVmq_listener = EVmqListener()
        self.EVmq_listener.moveToThread(self.thread)
        self.thread.started.connect(self.EVmq_listener.loop)
        self.EVmq_listener.message.connect(self.signal_received)
        QtCore.QTimer.singleShot(0, self.thread.start)

        self.marketComboBox.currentIndexChanged.connect(self.switchMarket)

    def switchMarket(self):
        choice = self.marketComboBox.currentText()
        if choice == "GDAX-BTC/USD":
            self.EVmq_listener.swap_topic_filter(b'{"exchange":"Gdax","instmt":"BTCUSD"')
        if choice == "GDAX-ETH/USD":
            self.EVmq_listener.swap_topic_filter(b'{"exchange":"Gdax","instmt":"ETHUSD"')
        if choice == "GDAX-LTC/USD":
            self.EVmq_listener.swap_topic_filter(b'{"exchange":"Gdax","instmt":"LTCUSD"')

    def signal_received(self, message):
        #self.debugTextEdit.append("%s\n" % message)

        # Get the current message
        msg_json = json.loads(message)

        # Update the current Price widget and color it based on last value
        if msg_json["trade_px"] > self.last_px:
            self.currentCoinPrice.setStyleSheet("color: green")
        elif msg_json["trade_px"] < self.last_px:
            self.currentCoinPrice.setStyleSheet("color: red")
        else:
            self.currentCoinPrice.setStyleSheet("color: white")
        self.last_px = msg_json["trade_px"]
        self.currentCoinPrice.setText(str(msg_json["trade_px"]))

        usd_value = self.last_px * self.coins_owned
        self.usdHeldValueLabel.setText('$ ' + str(usd_value))
        self.coinsHeldValueLabel.setText(str(self.coins_owned) + ' Coins')

        self.askListWidget.clear()
        self.askListWidget.addItem(str(msg_json["a5"]) + ' - ' + str(msg_json["aq5"]))
        self.askListWidget.addItem(str(msg_json["a4"]) + ' - ' + str(msg_json["aq4"]))
        self.askListWidget.addItem(str(msg_json["a3"]) + ' - ' + str(msg_json["aq3"]))
        self.askListWidget.addItem(str(msg_json["a2"]) + ' - ' + str(msg_json["aq2"]))
        self.askListWidget.addItem(str(msg_json["a1"]) + ' - ' + str(msg_json["aq1"]))

        self.bidListWidget.clear()
        self.bidListWidget.addItem(str(msg_json["b1"]) + ' - ' + str(msg_json["bq1"]))
        self.bidListWidget.addItem(str(msg_json["b2"]) + ' - ' + str(msg_json["bq2"]))
        self.bidListWidget.addItem(str(msg_json["b3"]) + ' - ' + str(msg_json["bq3"]))
        self.bidListWidget.addItem(str(msg_json["b4"]) + ' - ' + str(msg_json["bq4"]))
        self.bidListWidget.addItem(str(msg_json["b5"]) + ' - ' + str(msg_json["bq5"]))

        self.setWindowTitle(str(msg_json["trade_px"]) + ' - EVTrader v0.1')

    def closeEvent(self, event):
        self.zeromq_listener.running = False
        self.thread.quit()
        self.thread.wait()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    form = EV()
    form.show()
    app.exec_()
    form.close()


if __name__ == '__main__':
    main()
