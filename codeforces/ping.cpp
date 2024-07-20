#include <bits/stdc++.h>

using namespace std;

int main() {
    int session_len_hour = 6;
    int session_len_s = session_len_hour * 3600;
    int period_s = 15;
    for (int i = 0; i <= session_len_s / period_s; i++) {
        cout << "ping" << endl;
        sleep(period_s);
    }
    return 0;
}