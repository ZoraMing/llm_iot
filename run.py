import os
import subprocess


app_path = os.path.join('home_server', 'app.py')

# 运行 home_app/app.py
try:
    subprocess.run(['python', app_path])
except KeyboardInterrupt:
    print("Web app Exiting....")
except Exception as e:
    print("An error occurred:", str(e))
    print("Exiting.")
    exit(1)