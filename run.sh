git pull origin master
ps aux | grep app:app | awk '{print "kill -9 " $2}' | sh -x
setsid python -m uvicorn app:app --host 0.0.0.0 >> nohup.out 2>&1 &
tail -f nohup.out
