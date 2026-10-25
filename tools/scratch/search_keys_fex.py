import os, re

for root, dirs, files in os.walk('d:/v316cm/Firmware'):
    for f in files:
        if f.endswith('.fex') or f.endswith('.dts') or 'sys_config' in f:
            path = os.path.join(root, f)
            try:
                with open(path, 'r', errors='ignore') as fp:
                    content = fp.read()
                    if 'gpiokey' in content or 'powerkey' in content or 'gpio_key' in content or 'key' in content.lower():
                        print(f"Match in {path}:")
                        for line in content.splitlines():
                            if any(k in line.lower() for k in ['key', 'gpio', 'button', 'axp']):
                                if len(line.strip()) < 80:
                                    print("  ", line.strip())
            except Exception as e:
                pass
