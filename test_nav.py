from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    page.goto('http://119.29.128.18')
    page.wait_for_load_state('networkidle')
    
    # Login first
    page.evaluate('''async () => {
        await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: 'pwtest', password: 'test1234'})
        });
        localStorage.setItem('xc_token', 'session');
        localStorage.setItem('xc_user', 'pwtest');
    }''')
    
    # Reload to pick up login state
    page.reload()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)
    
    # Test logged-in state at different sizes
    for width in [1280, 900, 768, 600, 480]:
        page.set_viewport_size({'width': width, 'height': 800})
        page.wait_for_timeout(800)
        
        result = page.evaluate('''() => {
            var right = document.querySelector('.topnav-right');
            var theme = document.getElementById('themeToggleBtn');
            var avatar = document.querySelector('.nav-avatar-wrap');
            var loginBtn = document.querySelector('.nav-auth-btns');
            var themeIcon = document.getElementById('themeToggleIcon');
            var vw = window.innerWidth;
            var rr = right ? right.getBoundingClientRect() : null;
            var tr = theme ? theme.getBoundingClientRect() : null;
            var ar = avatar ? avatar.getBoundingClientRect() : null;
            return {
                rightVisible: rr && rr.x + rr.width <= vw && rr.x >= 0,
                themeVisible: tr && tr.x + tr.width <= vw && tr.x >= 0,
                themeText: themeIcon ? themeIcon.textContent : null,
                avatarVisible: ar && ar.x + ar.width <= vw && ar.x >= 0,
                hasAvatar: !!avatar,
                hasLoginBtn: !!loginBtn,
                rightX: rr ? rr.x : 0,
                rightW: rr ? rr.width : 0
            };
    }''')
        status = '✅' if result['rightVisible'] and result['themeVisible'] else '❌'
        avatar_s = '✅' if result['avatarVisible'] else ('👤hidden' if result['hasAvatar'] else '🔒login')
        print(f'{status} {width}px: right(x={result["rightX"]:.0f} w={result["rightW"]:.0f}) theme={result["themeText"]} avatar={avatar_s}')
    
    # Screenshot at 1280px logged in
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.wait_for_timeout(500)
    page.screenshot(path='test_loggedin_1280.png')
    
    # Screenshot at 600px
    page.set_viewport_size({'width': 600, 'height': 800})
    page.wait_for_timeout(500)
    page.screenshot(path='test_loggedin_600.png')
    
    browser.close()
