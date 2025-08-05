def parse_windows_line(line):
    try:
        parts = line.split(',')
        timestamp = parts[0].strip()
        level = parts[1].strip().upper()
        message = ','.join(parts[2:]).strip()
        return {
            "source": "Windows",
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "raw": line
        }
    except:
        return {
            "source": "Windows",
            "timestamp": "",
            "level": "INFO",
            "message": line,
            "raw": line
        }
