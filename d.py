import requests
import time
import datetime
from colorama import Fore, Style, init
from random import randint

# Initialize colorama
init(autoreset=True)

# Load accounts from data.txt
def load_accounts():
    accounts = []
    try:
        with open('data.txt', 'r') as file:
            lines = file.readlines()
            # Assuming each account has 2 lines: tgId and accessToken
            for i in range(0, len(lines), 2):
                tg_id = lines[i].strip()
                access_token = lines[i + 1].strip()
                accounts.append((tg_id, access_token))
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan.")
    return accounts

# Print welcome message
def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop DepinSim")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop")

# Countdown timer for 24 hours
def countdown_timer():
    end_time = datetime.datetime.now() + datetime.timedelta(days=1)
    while datetime.datetime.now() < end_time:
        remaining = end_time - datetime.datetime.now()
        print(Fore.YELLOW + f"Waktu tersisa untuk siklus selanjutnya: {remaining}", end='\r')
        time.sleep(1)

# Claim offline rewards
def claim_offline_rewards(user_id, access_token):
    headers = {"accesstoken": access_token}
    response = requests.post(f"https://api.depinsim.com/base/claimOfflineRewards/{user_id}", headers=headers)
    if response.status_code == 200:
        return response.json().get('data', {})
    else:
        print(Fore.RED + f"Gagal klaim rewards. Status: {response.status_code}")
        return {}

# Fetch user info
def fetch_user_info(user_id, access_token):
    headers = {"accesstoken": access_token}
    response = requests.post(f"https://api.depinsim.com/base/userInfo/{user_id}", headers=headers)
    if response.status_code == 200:
        user_info = response.json().get('data', {})
        # Display account response information
        print(Fore.GREEN + f"Username: {user_info.get('tgUserName')}")
        print(Fore.YELLOW + f"Level: {user_info.get('userLevel')} - {user_info.get('levelName')}")
        print(Fore.GREEN + f"Saldo Poin: {user_info.get('pointBalance')}")
        print(Fore.YELLOW + f"Saldo Penambangan: {user_info.get('miningBalance')}")
        return user_info
    else:
        print(Fore.RED + f"Error saat mengambil user info. Status: {response.status_code}")
        return {}

# Perform game tap session where each session exhausts todayEnergy
def perform_game_tap_session(user_id, today_boost_num, today_energy, access_token):
    headers = {"accesstoken": access_token}
    session_results = []

    while today_boost_num > 0:
        print(Fore.CYAN + f"\nMemulai sesi tap baru. Sisa Boost: {today_boost_num}, Energi: {today_energy}")
        taps_in_session = []

        while today_energy > 0:  # Continue while there is any energy remaining
            random_tap_value = randint(80, 200)

            # If energy is lower than the random tap value, use remaining energy for the tap
            if today_energy < random_tap_value:
                print(Fore.YELLOW + f"Energi tidak cukup untuk nilai tap sebesar {random_tap_value}. Menggunakan energi tersisa: {today_energy}")
                random_tap_value = today_energy  # Set tap value to the remaining energy

            response = requests.post(f"https://api.depinsim.com/base/tap/{user_id}/{random_tap_value}", headers=headers)
            if response.status_code == 200:
                tap_data = response.json().get('data', {})
                taps_in_session.append(tap_data)
                print(Fore.GREEN + f"Tap berhasil: Nilai Tap = {random_tap_value}, Energi Tersisa = {today_energy - random_tap_value}")
                
                today_energy -= random_tap_value
            else:
                print(Fore.RED + f"Tap gagal dengan Nilai Tap = {random_tap_value}. Status code:", response.status_code)
                break

            time.sleep(1)

        session_results.append(taps_in_session)

        # If energy is depleted, attempt to activate a boost
        if today_energy <= 0:
            print(Fore.YELLOW + "Energi habis, mencoba mengaktifkan boost baru...")
            boost_response = requests.post(f"https://api.depinsim.com/base/boost/{user_id}", headers=headers)
            if boost_response.status_code == 200 and boost_response.json().get("code") == 0:
                print(Fore.GREEN + "Boost berhasil diaktifkan.")
                
                # Refresh boost and energy status after activating boost
                user_info = fetch_user_info(user_id, access_token)
                today_boost_num = user_info.get("todayBoostNum", 0)
                today_energy = user_info.get("todayEnergy", 0)
            else:
                print(Fore.RED + "Gagal mengaktifkan boost baru.")
                break

        # If no more boosts are available, exit the loop
        if today_boost_num <= 0:
            print(Fore.RED + "Boosts habis untuk hari ini.")
            break

    print(Fore.CYAN + f"\nProses tap selesai. Total sesi tap: {len(session_results)}, Sisa Boost: {today_boost_num}")
    return session_results

# Handle task if the first completion attempt fails
def handle_task(user_id, task_id, access_token):
    headers = {"accesstoken": access_token}
    response = requests.post(f"https://api.depinsim.com/base/handleTask/{user_id}/{task_id}", headers=headers)
    if response.status_code == 200 and response.json().get("code") == 0:
        print(Fore.YELLOW + f"Tugas dengan ID {task_id} diproses dengan handleTask.")
        return True
    else:
        print(Fore.RED + f"Gagal menjalankan handleTask untuk ID {task_id}. Status: {response.status_code}")
        return False

# Complete a specific task with retry using handle_task
def complete_task(user_id, task_id, access_token):
    headers = {"accesstoken": access_token}

    # Attempt to handle the task first but continue regardless of success or failure
    print(Fore.YELLOW + f"Mencoba handleTask untuk tugas ID {task_id} sebelum menyelesaikan.")
    handle_task(user_id, task_id, access_token)  # Call handle_task but don't check for success

    # Proceed to attempt task completion
    response = requests.post(f"https://api.depinsim.com/base/checkTask/{user_id}/{task_id}", headers=headers)
    
    if response.status_code == 200 and response.json().get("code") == 0:
        task_result = response.json().get("data", {}).get("taskResult")
        if task_result == 2:
            print(Fore.GREEN + f"Tugas dengan ID {task_id} berhasil diselesaikan.")
            return True
        else:
            print(Fore.YELLOW + f"Tugas dengan ID {task_id} tidak sepenuhnya selesai setelah handleTask.")
    else:
        print(Fore.RED + f"Gagal menyelesaikan tugas dengan ID {task_id}. Status: {response.status_code}")

    return False

# Fetch task list for the user
def get_task_list(user_id, access_token):
    headers = {"accesstoken": access_token}
    response = requests.post(f"https://api.depinsim.com/base/taskList/{user_id}", headers=headers)
    if response.status_code == 200:
        tasks = response.json().get('data', {}).get('oneTimeTask', [])
        print(Fore.GREEN + "Daftar Tugas:")
        for task in tasks:
            action_name = task.get("action_name", "Tidak tersedia")
            text = task.get("text", "Tidak ada deskripsi")
            point_rewards = task.get("point_rewards", 0)
            task_result = task.get("task_result", None)
            if task_result == 0:
                print(Fore.CYAN + f" - {action_name}: {text} (Reward: {point_rewards} points)")
        return tasks
    else:
        print(Fore.RED + f"Gagal mengambil daftar tugas. Status: {response.status_code}")
        return []

# Process accounts with API requests
def process_accounts():
    accounts = load_accounts()
    account_count = len(accounts)
    print(Fore.CYAN + f"Jumlah akun yang akan diproses: {account_count}")

    for idx, (user_id, access_token) in enumerate(accounts, 1):
        try:
            print(Fore.GREEN + f"\nMemproses akun ke-{idx} dari {account_count}: {user_id}")

            # Fetch user information
            user_info = fetch_user_info(user_id, access_token)
            if user_info is None:
                print(Fore.RED + f"Gagal mengambil informasi pengguna untuk akun {user_id}. Melanjutkan ke akun berikutnya.")
                continue

            # Claim rewards if available
            rewards_data = claim_offline_rewards(user_id, access_token)
            print(Fore.GREEN + f"Rewards diklaim: {rewards_data.get('pointBalance', 'Tidak ada poin')}")

            # Process tasks
            task_list = get_task_list(user_id, access_token)
            for task in task_list:
                if task.get("task_result") == 0:
                    complete_task(user_id, task.get("id"), access_token)
                    time.sleep(1)

            # Get play credits and energy values
            today_boost_num = user_info.get("todayBoostNum", 0)
            today_energy = user_info.get("todayEnergy", 0)

            # Initiate tapping sessions if boosts and energy are available
            if today_boost_num > 0 and today_energy > 0:
                tap_sessions = perform_game_tap_session(user_id, today_boost_num, today_energy, access_token)
                print(Fore.GREEN + f"Sesi tap selesai: {len(tap_sessions)} sesi berhasil.")

            time.sleep(5)

        except Exception as e:
            print(Fore.RED + f"Terjadi kesalahan pada akun ke-{idx}: {str(e)}")
            continue

    print(Fore.CYAN + "\nSemua akun telah diproses, memulai hitung mundur 24 jam...")
    countdown_timer()

# Main loop
if __name__ == "__main__":
    print_welcome_message()
    while True:
        process_accounts()
