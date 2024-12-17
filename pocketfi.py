import os
import json
import time
import requests
from pathlib import Path
from urllib.parse import unquote, parse_qs
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama
init(autoreset=True)


class PocketFi:
    def __init__(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://pocketfi.app",
            "Referer": "https://pocketfi.app/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.6 Mobile/15E148 Safari/604.1"
            ),
            "X-Paf-T": "Abvx2NzMTM==",
        }

    def log(self, msg, msg_type="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if msg_type == "success":
            color = Fore.GREEN
            prefix = "[*]"
        elif msg_type == "custom":
            color = Fore.MAGENTA
            prefix = "[*]"
        elif msg_type == "error":
            color = Fore.RED
            prefix = "[!]"
        elif msg_type == "warning":
            color = Fore.YELLOW
            prefix = "[*]"
        else:
            color = Fore.BLUE
            prefix = "[*]"
        print(f"[{timestamp}] {prefix} {color}{msg}{Style.RESET_ALL}")

    def countdown(self, seconds):
        for remaining in range(seconds, -1, -1):
            mins, secs = divmod(remaining, 60)
            hrs, mins = divmod(mins, 60)
            time_str = f"{hrs:02}:{mins:02}:{secs:02}"
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] [*] Wait {time_str} to continue...",
                end="\r",
            )
            time.sleep(1)
        print("")  # Move to the next line after countdown

    def get_user_mining(self, init_data):
        url = "https://gm.pocketfi.org/mining/getUserMining"
        headers = self.headers.copy()
        headers["Telegramrawdata"] = init_data

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("userMining")
        except requests.RequestException as e:
            self.log(f"Lỗi user: {str(e)}", "error")
            return None

    def claim_mining(self, init_data):
        url = "https://gm.pocketfi.org/mining/claimMining"
        headers = self.headers.copy()
        headers["Telegramrawdata"] = init_data

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            balance = data.get("userMining", {}).get("gotAmount", "0")
            self.log(f"Claim successful | Balance: {balance}", "success")
        except requests.RequestException as e:
            self.log(f"Error Claim: {str(e)}", "error")

    def get_tasks(self, boost_type, init_data):
        url = f"https://bot.pocketfi.org/boost/tasks?boostType={boost_type}"
        headers = self.headers.copy()
        headers["Telegramrawdata"] = init_data

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.log(f"Error {boost_type} task: {str(e)}", "error")
            return None

    def do_task(self, task_id, init_data):
        url = "https://bot.pocketfi.org/confirmSubscription"
        headers = self.headers.copy()
        headers["Telegramrawdata"] = init_data

        data = {
            "subscriptionType": task_id,
        }
    
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 500:
                self.log("You have to complete the task manually.", "warning")
            else:
                response.raise_for_status()
                self.log(f"Complete the mission {task_id}...", "success")
        except requests.RequestException as e:
            self.log(f"Task error: {str(e)}", "error")

    def manage_task(self, init_data):
        pump_task = self.get_tasks("pump", init_data)
        general_task = self.get_tasks("general", init_data)
        partner_task = self.get_tasks("partner", init_data)

        if not all([pump_task, general_task, partner_task]):
            self.log("Unable to get quest information.", "error")
            return

        try:
            all_tasks = (
                pump_task.get("tasks", {}).get("pump", [])
                + general_task.get("tasks", {}).get("connect", [])
                + general_task.get("tasks", {}).get("daily", [])
                + general_task.get("tasks", {}).get("subscriptions", [])
                + general_task.get("tasks", {}).get("trade", [])
                + partner_task.get("tasks", {}).get("partner", [])
            )
        except AttributeError as e:
            self.log(f"Error in combining tasks: {str(e)}", "error")
            return

        for task in all_tasks:
            if task.get("doneAmount") == 0:
                task_code = task.get("code", "Unknown")
                self.log(f"Start task {task_code}...", "warning")
                self.do_task(task_code, init_data)

    def main(self):
        data_file = Path(__file__).parent / "data.txt"
        if not data_file.exists():
            self.log("data.txt file not found", "error")
            return

        with data_file.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            self.log("File data.txt trống.", "error")
            return

        while True:
            for index, init_data in enumerate(lines, start=1):
                try:
                    parsed_data = parse_qs(init_data)
                    user_encoded = parsed_data.get("user", [None])[0]
                    if not user_encoded:
                        self.log(f"Account {index}: User information not found.", "error")
                        continue
                    user_data = json.loads(unquote(user_encoded))
                    user_name = user_data.get("username", "Unknown")
                except (json.JSONDecodeError, IndexError, TypeError) as e:
                    self.log(f"Account {index}: Error parsing user data: {str(e)}", "error")
                    continue

                print(f"\n========== Account {index} | {Fore.GREEN}{user_name}{Style.RESET_ALL} ==========")

                user_mining = self.get_user_mining(init_data)

                if user_mining:
                    got_amount = user_mining.get("gotAmount", "0")
                    speed = user_mining.get("speed", "0")
                    mining_amount = user_mining.get("miningAmount", "0")

                    self.log(f"Balance: {got_amount}", "success")
                    self.log(f"Speed: {speed}", "success")
                    self.log(f"Mining score: {mining_amount}", "success")

                    self.log("Start claiming...")
                    self.claim_mining(init_data)

                    self.log("Start the mission...")
                    self.manage_task(init_data)
                else:
                    self.log(f"Account {index}: Unable to get mining information.", "error")

            self.log("Wait 5 hours to continue...", "info")
            self.countdown(5 * 60 * 60)  # 5 hours in seconds


if __name__ == "__main__":
    pocket_fi = PocketFi()
    try:
        pocket_fi.main()
    except KeyboardInterrupt:
        print("\n Siap bos. dimatikan botnya.")
    except Exception as e:
        print(f"{Fore.RED}Exception Error: {str(e)}{Style.RESET_ALL}")
