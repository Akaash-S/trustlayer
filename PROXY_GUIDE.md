# TrustLayer Proxy Setup (No API Keys)

This mode allows you to use **ChatGPT, Gemini, or Claude** directly in your browser while TrustLayer protects your data in the background.

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Start the Proxy
Run this command in your terminal. It will start a web interface at `http://localhost:8081` and the proxy at `localhost:8080`.

```bash
mitmweb -s proxy_addon.py --listen-port 8080
```

## 3. Configure Your Computer/Browser
You need to tell your computer to send traffic through TrustLayer.

**Windows:**
1.  Search "Proxy Settings" in Start Menu.
2.  Enable **"Use a proxy server"**.
3.  Address: `127.0.0.1`, Port: `8080`.
4.  Click Save.

## 4. Install the Security Certificate (Crucial!)
Since AI sites use HTTPS, you must trust the proxy.

1.  Open your browser (Chrome/Edge).
2.  Visit: [http://mitm.it](http://mitm.it)
    *   *Note: This page only loads if the proxy (Step 2 & 3) is working.*
3.  Click **Windows** (Download certificate).
4.  Open the file -> **Install Certificate**.
5.  Select **Local Machine**.
6.  Select **"Place all certificates in the following store"** -> **Trusted Root Certification Authorities**.
7.  Finish.

## 5. Test It
1.  Go to `https://chatgpt.com`.
2.  Type: "My name is John Doe."
3.  Look at the `mitmweb` terminal/page. You will see the request was intercepted!
4.  ChatGPT will receive: "My name is [PERSON_1]."
5.  You will see: "My name is John Doe." (Magic!)
