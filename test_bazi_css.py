from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto('http://119.29.128.18')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    page.evaluate('''async () => {
        const form = new FormData();
        form.append('username', 'pwtest');
        form.append('password', 'test1234');
        await fetch('/api/login', { method: 'POST', body: form });
    }''')
    page.reload()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    sidebar_btn = page.query_selector('.topnav-sidebar-btn')
    if sidebar_btn:
        sidebar_btn.click()
        page.wait_for_timeout(1000)
    
    page.evaluate('''() => {
        var items = document.querySelectorAll('.sidebar-item-body');
        for (var i = 0; i < items.length; i++) {
            var onclick = items[i].getAttribute('onclick') || '';
            if (onclick.indexOf('_showBaziConvDetail') > -1) {
                items[i].click();
                return;
            }
        }
    }''')
    page.wait_for_timeout(3000)
    
    # Deep inspect CSS
    result = page.evaluate('''() => {
        var userBubble = document.querySelector('#baiChatContainer .chat-bubble-user');
        if (!userBubble) return { error: 'no bubble' };
        var cs = getComputedStyle(userBubble);
        
        // Check all matching CSS rules
        var rules = [];
        for (var i = 0; i < document.styleSheets.length; i++) {
            try {
                var sheet = document.styleSheets[i];
                for (var j = 0; j < sheet.cssRules.length; j++) {
                    var rule = sheet.cssRules[j];
                    if (rule.selectorText && rule.selectorText.indexOf('chat-bubble-user') > -1) {
                        rules.push({
                            selector: rule.selectorText,
                            cssText: rule.cssText.substring(0, 150),
                            matches: userBubble.matches(rule.selectorText)
                        });
                    }
                }
            } catch(e) {}
        }
        
        return {
            padding: cs.padding,
            fontSize: cs.fontSize,
            height: userBubble.getBoundingClientRect().height,
            width: userBubble.getBoundingClientRect().width,
            display: cs.display,
            color: cs.color,
            background: cs.backgroundColor,
            rules: rules
        };
    }''')
    print(f'padding: {result["padding"]}')
    print(f'fontSize: {result["fontSize"]}')
    print(f'height: {result["height"]}')
    print(f'width: {result["width"]}')
    print(f'display: {result["display"]}')
    print(f'color: {result["color"]}')
    print(f'background: {result["background"]}')
    print(f'\nMatching CSS rules:')
    for r in result['rules']:
        print(f'  matches={r["matches"]}: {r["selector"]}')
        print(f'    {r["cssText"][:120]}')
    
    browser.close()
