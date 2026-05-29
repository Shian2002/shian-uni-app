from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto('http://119.29.128.18')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    # Login
    page.evaluate('''async () => {
        const form = new FormData();
        form.append('username', 'pwtest');
        form.append('password', 'test1234');
        await fetch('/api/login', { method: 'POST', body: form });
    }''')
    page.reload()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    # Open sidebar
    sidebar_btn = page.query_selector('.topnav-sidebar-btn')
    if sidebar_btn:
        sidebar_btn.click()
        page.wait_for_timeout(1000)
    
    # Find and click first bazi conversation
    clicked = page.evaluate('''() => {
        var items = document.querySelectorAll('.sidebar-item-body');
        for (var i = 0; i < items.length; i++) {
            var onclick = items[i].getAttribute('onclick') || '';
            if (onclick.indexOf('_showBaziConvDetail') > -1) {
                items[i].click();
                return onclick;
            }
        }
        return null;
    }''')
    print(f'Clicked: {clicked}')
    page.wait_for_timeout(3000)
    
    # Check what's rendered in the chat area
    result = page.evaluate('''() => {
        var container = document.getElementById('baiChatContainer');
        if (!container) return { error: 'no baiChatContainer' };
        var children = container.children;
        var items = [];
        for (var i = 0; i < children.length; i++) {
            var el = children[i];
            items.push({
                tag: el.tagName,
                className: el.className,
                text: el.textContent.trim().substring(0, 80),
                innerHTML: el.innerHTML.substring(0, 120),
                display: getComputedStyle(el).display,
                visibility: getComputedStyle(el).visibility,
                height: el.getBoundingClientRect().height
            });
        }
        return { count: items.length, items: items };
    }''')
    print(f'\nChat container children: {result.get("count", 0)}')
    for item in result.get('items', []):
        print(f'  [{item["className"]}] display={item["display"]} h={item["height"]:.0f}')
        print(f'    text: {item["text"][:60]}')
        print(f'    html: {item["innerHTML"][:80]}')
    
    page.screenshot(path='bazi_user_msg.png')
    print('\nScreenshot saved')
    browser.close()
