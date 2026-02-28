#!/usr/bin/env python3
"""
X Patrol Scraper — 抓取推荐页 + 收藏夹
通过 Chrome CDP (port 9222) 抓取，输出 JSON 到 /tmp/x-patrol-raw.json
"""
import json, asyncio, sys, time, argparse, os

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

import urllib.request

msg_id = 0

def get_ws_url(port):
    """Get WebSocket URL for the first page tab"""
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5).read())
    for t in tabs:
        if t['type'] == 'page':
            return t['webSocketDebuggerUrl']
    raise Exception("No page tab found on CDP")

async def send_cmd(ws, method, params=None):
    global msg_id
    msg_id += 1
    cmd = {"id": msg_id, "method": method}
    if params:
        cmd["params"] = params
    await ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
        if resp.get("id") == msg_id:
            return resp

EXTRACT_JS = """
(() => {
    const tweets = [];
    const articles = document.querySelectorAll('article[data-testid="tweet"]');
    articles.forEach(article => {
        try {
            const userLink = article.querySelector('a[href^="/"][role="link"] span');
            const handleEl = article.querySelector('a[href^="/"][tabindex="-1"]');
            const author = userLink ? userLink.textContent : '';
            const handle = handleEl ? handleEl.getAttribute('href') : '';
            const textEl = article.querySelector('[data-testid="tweetText"]');
            const text = textEl ? textEl.textContent : '';
            const timeEl = article.querySelector('time');
            const linkEl = timeEl ? timeEl.closest('a') : null;
            const link = linkEl ? linkEl.getAttribute('href') : '';
            const metrics = {};
            const groups = article.querySelectorAll('[role="group"] button');
            const metricNames = ['replies', 'reposts', 'likes', 'views'];
            groups.forEach((btn, i) => {
                const val = btn.querySelector('[data-testid]');
                if (val && i < metricNames.length) {
                    metrics[metricNames[i]] = val.textContent || '0';
                }
            });
            const imgs = article.querySelectorAll('[data-testid="tweetPhoto"] img');
            if (text || author) {
                tweets.push({
                    author, handle, text: text.substring(0, 800),
                    link: link ? 'https://x.com' + link : '',
                    metrics, images: imgs.length,
                    timestamp: timeEl ? timeEl.getAttribute('datetime') : ''
                });
            }
        } catch(e) {}
    });
    return JSON.stringify(tweets);
})()
"""

async def scrape_page(ws, url, scroll_times, label):
    """Navigate to URL and scrape tweets by scrolling"""
    print(f"[{label}] Navigating to {url}...", file=sys.stderr)
    await send_cmd(ws, "Page.navigate", {"url": url})
    await asyncio.sleep(12)  # Increased wait time for slow loading

    # Check page title
    result = await send_cmd(ws, "Runtime.evaluate", {
        "expression": "document.title", "returnByValue": True
    })
    title = result.get('result', {}).get('result', {}).get('value', '')
    print(f"[{label}] Page title: {title}", file=sys.stderr)

    if 'login' in title.lower() or 'log in' in title.lower():
        print(f"[{label}] ERROR: Not logged in!", file=sys.stderr)
        return []

    all_tweets = []
    seen_ids = set()

    for i in range(scroll_times):
        try:
            result = await send_cmd(ws, "Runtime.evaluate", {
                "expression": EXTRACT_JS, "returnByValue": True
            })
            raw = result.get('result', {}).get('result', {}).get('value', '[]')
            tweets = json.loads(raw)

            for t in tweets:
                tid = t.get('link', '') or t.get('text', '')[:80]
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_tweets.append(t)

            print(f"[{label}] Scroll {i+1}/{scroll_times}, unique: {len(all_tweets)}", file=sys.stderr)

            await send_cmd(ws, "Runtime.evaluate", {
                "expression": "window.scrollBy(0, window.innerHeight * 2)"
            })
            await asyncio.sleep(4)  # Increased scroll wait
        except Exception as e:
            print(f"[{label}] Error on scroll {i+1}: {e}", file=sys.stderr)
            break

    return all_tweets

async def main(port):
    ws_url = get_ws_url(port)
    print(f"Connecting to {ws_url}", file=sys.stderr)

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Scrape feed
        feed = await scrape_page(ws, "https://x.com/home", 12, "Feed")

        # Scrape bookmarks
        bookmarks = await scrape_page(ws, "https://x.com/i/bookmarks", 8, "Bookmarks")

        results = {
            "feed": feed,
            "bookmarks": bookmarks,
            "feed_count": len(feed),
            "bookmarks_count": len(bookmarks),
            "timestamp": time.strftime("%Y-%m-%d %H:%M")
        }

        # Write to file
        out_path = "/tmp/x-patrol-raw.json"
        with open(out_path, 'w') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\nDone: feed={len(feed)}, bookmarks={len(bookmarks)}, saved to {out_path}", file=sys.stderr)

        # Also print JSON to stdout for piping
        print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9222, help="CDP port")
    args = parser.parse_args()
    asyncio.run(main(args.port))
