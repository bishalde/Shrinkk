from user_agents import parse


def parse_request_data(request):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    ua_string = request.headers.get("User-Agent", "")
    ua = parse(ua_string)

    device = "Desktop"
    if ua.is_mobile:
        device = "Mobile"
    elif ua.is_tablet:
        device = "Tablet"

    browser = ua.browser.family or "Unknown"
    os = ua.os.family or "Unknown"
    referrer = request.referrer or "Direct"

    country = None
    city = None

    return {
        "ip": ip,
        "country": country,
        "city": city,
        "device": device,
        "browser": browser,
        "os": os,
        "referrer": referrer,
    }
