import subprocess
import platform

def get_cpu_name():
    system = platform.system()
    
    if system == "Windows":
        # 方案1：wmic（最通用）
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "Name"],
                capture_output=True, text=True, check=True, timeout=5
            )
            lines = [line.strip() for line in result.stdout.splitlines() 
                     if line.strip() and line.strip() != "Name"]
            if lines:
                return lines[0]
        except Exception:
            pass
        
        # 方案2：注册表（wmic 被精简后的系统备用）
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            return name.strip()
        except Exception:
            pass
    
    elif system == "Linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
    
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, check=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            pass
    
    # 兜底
    proc = platform.processor()
    return proc if proc else "Unknown"


if __name__ == "__main__":
    print(f"CPU: {get_cpu_name()}")
