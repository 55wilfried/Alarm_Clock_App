import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, \
    QPushButton, QLineEdit, QGridLayout, QTimeEdit, QListWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import QTimer, QTime, QDate, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout
from PyQt5.QtCore import QUrl


class AlarmClockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Alarm Clock App')
        self.setGeometry(100, 100, 800, 600)

        # Determine the path to the icons directory and sound file
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        icon_path = os.path.join(base_path, 'icons')
        sound_path = os.path.join(base_path, 'sounds', 'sound.wav')

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Icons for tabs
        self.tabs.addTab(self.create_alarm_page(), QIcon(os.path.join(icon_path, 'alarm.png')), 'Alarm')
        self.tabs.addTab(self.create_clock_page(), QIcon(os.path.join(icon_path, 'clock.png')), 'Clock')
        self.tabs.addTab(self.create_timer_page(), QIcon(os.path.join(icon_path, 'timer.png')), 'Timer')
        self.tabs.addTab(self.create_stopwatch_page(), QIcon(os.path.join(icon_path, 'stopwatch.png')), 'Stopwatch')

        # Add tooltips to each tab
        self.tabs.setTabToolTip(0, "Alarms.")
        self.tabs.setTabToolTip(1, "Clock")
        self.tabs.setTabToolTip(2, "Timer")
        self.tabs.setTabToolTip(3, "Stopwatch")

        # Initialize alarm-related variables
        self.alarm_time_to_set = []
        self.alarm_timer = QTimer()
        self.alarm_timer.timeout.connect(self.check_alarm)

        # Start a timer to check the alarm every second
        self.alarm_timer.start(1000)

        # Load alarm sound
        self.alarm_sound = QSoundEffect()
        self.alarm_sound.setSource(QUrl.fromLocalFile(sound_path))
        # Initialize timer sound
        self.timer_sound = QSoundEffect()
        self.timer_sound.setSource(QUrl.fromLocalFile(sound_path))

    def create_alarm_page(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Alarm time input with AM/PM
        self.alarm_time = QTimeEdit()
        self.alarm_time.setDisplayFormat('hh:mm:ss AP')  # 12-hour format with AM/PM
        layout.addWidget(QLabel('Set Alarm Time:'))
        layout.addWidget(self.alarm_time)

        # Set Alarm Button
        self.alarm_button = QPushButton('Set Alarm')
        self.alarm_button.clicked.connect(self.set_alarm)
        layout.addWidget(self.alarm_button)

        # List Widget to display set alarms with action buttons
        self.alarm_list = QListWidget()
        layout.addWidget(self.alarm_list)

        widget.setLayout(layout)
        return widget

    def create_clock_page(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Display Day, Date, and Time
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 30))
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        self.date_label = QLabel()
        self.date_label.setFont(QFont("Arial", 24))
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)

        self.update_clock()
        widget.setLayout(layout)
        return widget

    def create_timer_page(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Editable timer display in 00:00:00 format
        self.timer_display = QLineEdit('00:00:00')
        self.timer_display.setFont(QFont("Arial", 30))
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setMaxLength(8)
        self.timer_display.setInputMask('00:00:00')  # Input mask for format
        self.timer_display.editingFinished.connect(self.update_timer_from_display)
        layout.addWidget(self.timer_display)

        # Number buttons layout
        grid_layout = QGridLayout()
        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('0', 3, 1)
        ]

        for text, row, col in buttons:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, t=text: self.add_digit(t))  # Capture text `t` correctly
            grid_layout.addWidget(button, row, col)

        layout.addLayout(grid_layout)

        # Buttons to start and stop the timer
        self.start_button = QPushButton('Start Timer')
        self.start_button.clicked.connect(self.start_timer)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Timer')
        self.stop_button.clicked.connect(self.stop_timer)
        layout.addWidget(self.stop_button)

        # Horizontal layout for Clear Input and Stop Sound buttons
        button_row_layout = QHBoxLayout()
        self.clear_button = QPushButton('Clear Input')
        self.clear_button.clicked.connect(self.clear_time_input)
        button_row_layout.addWidget(self.clear_button)

        self.stop_sound_button = QPushButton('Stop Sound')
        self.stop_sound_button.clicked.connect(self.stop_timer_sound)
        button_row_layout.addWidget(self.stop_sound_button)

        # Add the horizontal layout to the main layout
        layout.addLayout(button_row_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.remaining_seconds = 0

        widget.setLayout(layout)
        return widget

    def add_digit(self, digit):
        cursor_position = self.timer_display.cursorPosition()
        current_text = self.timer_display.text().replace(':', '')

        # Insert the digit at the current cursor position or replace the digit at that position
        if len(current_text) < 6:
            new_text = (
                current_text[:cursor_position] + digit + current_text[cursor_position + 1:]
                if cursor_position < len(current_text) else
                current_text + digit
            )
            new_text = new_text[:6]  # Ensure it remains no longer than 6 digits

            # Update the timer display and set the cursor position
            self.timer_display.setText(f"{new_text[:2]}:{new_text[2:4]}:{new_text[4:6]}")
            self.timer_display.setCursorPosition(cursor_position + 1)

        # Update the remaining time based on the new input
        self.update_timer_from_display()

    def stop_timer_sound(self):
        """Stop the timer sound"""
        self.timer_display.setText('00:00:00')
        self.timer_sound.stop()

    def clear_time_input(self):
        self.timer_display.setText('00:00:00')
        self.timer.stop()  # Stop the timer when input is cleared
        self.remaining_seconds = 0  # Reset remaining seconds

    def start_timer(self):
        time_str = self.timer_display.text()
        self.remaining_seconds = self.parse_time_str(time_str)
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()

    def update_timer_from_display(self):
        time_str = self.timer_display.text()
        self.remaining_seconds = self.parse_time_str(time_str)

    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            time_str = QTime(0, 0).addSecs(self.remaining_seconds).toString('hh:mm:ss')
            self.timer_display.setText(time_str)
        else:
            self.timer.stop()
            self.timer_display.setText("Time's up!")
            # Play timer sound continuously
            self.timer_sound.setLoopCount(QSoundEffect.Infinite)
            self.timer_sound.play()

    def parse_time_str(self, time_str):
        """Parse time string (HH:MM:SS) into total seconds"""
        time = QTime.fromString(time_str, 'hh:mm:ss')
        return time.hour() * 3600 + time.minute() * 60 + time.second()

    def create_stopwatch_page(self):
        widget = QWidget()
        main_layout = QVBoxLayout()

        # Create a horizontal layout for the stopwatch label
        label_layout = QHBoxLayout()
        self.stopwatch_label = QLabel('00:00:00')
        self.stopwatch_label.setFont(QFont("Arial", 30))
        self.stopwatch_label.setAlignment(Qt.AlignCenter)
        label_layout.addWidget(self.stopwatch_label)
        label_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(label_layout)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        self.start_stopwatch_button = QPushButton('Start')
        self.start_stopwatch_button.clicked.connect(self.start_stopwatch)
        button_layout.addWidget(self.start_stopwatch_button)

        self.stop_stopwatch_button = QPushButton('Stop')
        self.stop_stopwatch_button.clicked.connect(self.stop_stopwatch)
        button_layout.addWidget(self.stop_stopwatch_button)

        self.reset_stopwatch_button = QPushButton('Reset')
        self.reset_stopwatch_button.clicked.connect(self.reset_stopwatch)
        button_layout.addWidget(self.reset_stopwatch_button)

        button_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(button_layout)

        self.stopwatch_timer = QTimer()
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)
        self.stopwatch_time = QTime(0, 0)

        widget.setLayout(main_layout)
        return widget

    def set_alarm(self):
        """Set the alarm time"""
        alarm_time = self.alarm_time.time()
        if alarm_time not in self.alarm_time_to_set:
            self.alarm_time_to_set.append(alarm_time)

            # Create a QWidget to hold the alarm time and buttons
            alarm_item_widget = QWidget()
            alarm_item_layout = QHBoxLayout()

            # Label to display the alarm time
            alarm_label = QLabel(alarm_time.toString('hh:mm:ss AP'))
            alarm_item_layout.addWidget(alarm_label)

            # Edit Button
            edit_button = QPushButton('Edit')
            edit_button.clicked.connect(lambda: self.edit_alarm(alarm_label, alarm_time))
            alarm_item_layout.addWidget(edit_button)

            # Delete Button
            delete_button = QPushButton('Delete')
            delete_button.clicked.connect(lambda: self.delete_alarm(alarm_label, alarm_time))
            alarm_item_layout.addWidget(delete_button)

            alarm_item_widget.setLayout(alarm_item_layout)

            # Add the widget to QListWidget
            item = QListWidgetItem(self.alarm_list)
            self.alarm_list.addItem(item)
            self.alarm_list.setItemWidget(item, alarm_item_widget)
            item.setSizeHint(alarm_item_widget.sizeHint())

            print(f"Alarm set for: {alarm_time.toString('hh:mm:ss AP')}")

    def delete_alarm(self, alarm_label, alarm_time):
        """Delete the selected alarm"""
        # Debugging: Print the current list of alarm times
        print(f"Current alarm times: {[time.toString('hh:mm:ss AP') for time in self.alarm_time_to_set]}")
        print(f"Attempting to delete: {alarm_time.toString('hh:mm:ss AP')}")

        # Remove the alarm from the QListWidget
        for i in range(self.alarm_list.count()):
            item = self.alarm_list.item(i)
            widget = self.alarm_list.itemWidget(item)
            if widget.findChild(QLabel).text() == alarm_label.text():
                self.alarm_list.takeItem(self.alarm_list.row(item))
                if alarm_time in self.alarm_time_to_set:
                    self.alarm_time_to_set.remove(alarm_time)
                    print(f"Alarm deleted: {alarm_time.toString('hh:mm:ss AP')}")
                else:
                    print(f"Alarm time {alarm_time.toString('hh:mm:ss AP')} not found in list")
                break

    def edit_alarm(self, alarm_label, alarm_time):
        """Edit the alarm time using a custom dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Alarm")

        layout = QVBoxLayout()

        # QTimeEdit for selecting the new alarm time
        new_time_edit = QTimeEdit()
        new_time_edit.setTime(alarm_time)
        layout.addWidget(new_time_edit)

        # Dialog buttons for OK and Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        # Show dialog and get the result
        if dialog.exec_() == QDialog.Accepted:
            new_time = new_time_edit.time()

            # Update the alarm label
            alarm_label.setText(new_time.toString('hh:mm:ss AP'))

            # Update the alarm time in the list
            if alarm_time in self.alarm_time_to_set:
                index = self.alarm_time_to_set.index(alarm_time)
                self.alarm_time_to_set[index] = new_time
                print(f"Alarm edited to: {new_time.toString('hh:mm:ss AP')}")
            else:
                print(f"Alarm time {alarm_time.toString('hh:mm:ss AP')} not found in list")

    def check_alarm(self):
        """Check if the alarm should ring"""
        print("Checking alarms...")
        current_time = QTime.currentTime()
        alarms_to_remove = []

        for alarm_time in self.alarm_time_to_set:
            if (current_time.hour() == alarm_time.hour() and
                    current_time.minute() == alarm_time.minute() and
                    current_time.second() == alarm_time.second()):
                print(f"Alarm time matched: {alarm_time.toString('hh:mm:ss AP')}")
                self.show_alarm_dialog(alarm_time)
                alarms_to_remove.append(alarm_time)  # Collect alarms to be removed after checking

        # Remove alarms after checking
        for alarm_time in alarms_to_remove:
            if alarm_time in self.alarm_time_to_set:
                self.alarm_time_to_set.remove(alarm_time)

    def show_alarm_dialog(self, alarm_time):
        """Show a dialog when the alarm rings"""
        reply = QMessageBox(self)
        reply.setWindowTitle('Alarm')
        reply.setText('Alarm ringing! Do you want to snooze or delete it?')
        snooze_button = reply.addButton('Snooze', QMessageBox.ActionRole)
        delete_button = reply.addButton('Delete', QMessageBox.DestructiveRole)
        reply.setIcon(QMessageBox.Warning)

        # Play the alarm sound continuously
        self.alarm_sound.setLoopCount(QSoundEffect.Infinite)  # Loop indefinitely
        self.alarm_sound.play()

        # Show the dialog and get the result
        result = reply.exec_()

        # Stop the alarm sound when the dialog is closed
        self.alarm_sound.stop()

        if reply.clickedButton() == snooze_button:
            self.snooze_alarm()
        elif reply.clickedButton() == delete_button:
            # Find the corresponding alarm widget and remove it
            for index in range(self.alarm_list.count()):
                item = self.alarm_list.item(index)
                alarm_widget = self.alarm_list.itemWidget(item)
                alarm_label = alarm_widget.findChild(QLabel)
                if alarm_label and alarm_label.text() == alarm_time.toString('hh:mm:ss AP'):
                    self.delete_alarm(alarm_label, alarm_time)
                    break

    def snooze_alarm(self):
        """Snooze the alarm by 5 minutes"""
        current_time = QTime.currentTime()
        snooze_time = current_time.addSecs(300)  # 5 minutes later
        self.alarm_time_to_set.append(snooze_time)
        print(f"Alarm snoozed to: {snooze_time.toString('hh:mm:ss AP')}")

    def update_clock(self):
        """Update the clock display every second"""
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        self.time_label.setText(current_time.toString('hh:mm:ss AP'))
        self.date_label.setText(current_date.toString('dddd, MMMM d, yyyy'))
        QTimer.singleShot(1000, self.update_clock)

    def start_stopwatch(self):
        """Start the stopwatch"""
        self.stopwatch_timer.start(1000)

    def stop_stopwatch(self):
        """Stop the stopwatch"""
        self.stopwatch_timer.stop()

    def reset_stopwatch(self):
        """Reset the stopwatch"""
        self.stopwatch_timer.stop()
        self.stopwatch_time = QTime(0, 0)
        self.stopwatch_label.setText('00:00:00')

    def update_stopwatch(self):
        """Update the stopwatch display every second"""
        self.stopwatch_time = self.stopwatch_time.addSecs(1)
        self.stopwatch_label.setText(self.stopwatch_time.toString('hh:mm:ss'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlarmClockApp()
    window.show()
    sys.exit(app.exec_())
