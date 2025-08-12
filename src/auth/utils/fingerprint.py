import platform
import hashlib
import subprocess
import sys
import os
import uuid
import socket
import json
from typing import Dict, Optional

class DeviceFingerprint:
    """
    Advanced device fingerprinting system để tạo unique device ID
    Kết hợp nhiều hardware components để tạo fingerprint khó fake
    """
    
    def __init__(self):
        self.system = platform.system()
        self.fingerprint_data = {}
    
    def _run_subprocess_hidden(self, cmd, **kwargs):
        """Run subprocess with hidden console window on Windows"""
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
        
        return subprocess.run(cmd, **kwargs)
        
    def get_cpu_info(self) -> str:
        """Lấy thông tin CPU"""
        try:
            if self.system == "Windows":
                result = self._run_subprocess_hidden(['wmic', 'cpu', 'get', 'ProcessorId'], 
                                      capture_output=True, text=True, timeout=10)
                cpu_id = result.stdout.strip().split('\n')[-1].strip()
                if cpu_id and cpu_id != "ProcessorId":
                    return cpu_id
            
            elif self.system == "Linux":
                # Đọc từ /proc/cpuinfo
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'serial' in line.lower():
                            return line.split(':')[1].strip()
                        if 'processor' in line.lower() and '0' in line:
                            # Fallback: lấy model name
                            continue
                            
            elif self.system == "Darwin":  # macOS
                result = self._run_subprocess_hidden(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True, timeout=10)
                return result.stdout.strip()
                
        except Exception:
            pass
        
        # Fallback
        return f"{platform.processor()}_{platform.machine()}"
    
    def get_motherboard_info(self) -> str:
        """Lấy thông tin motherboard/system board"""
        try:
            if self.system == "Windows":
                # Lấy motherboard serial
                result = self._run_subprocess_hidden(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                      capture_output=True, text=True, timeout=10)
                mb_serial = result.stdout.strip().split('\n')[-1].strip()
                
                if mb_serial and mb_serial not in ["SerialNumber", "To be filled by O.E.M."]:
                    return mb_serial
                
                # Fallback: BIOS UUID
                result = self._run_subprocess_hidden(['wmic', 'csproduct', 'get', 'uuid'], 
                                      capture_output=True, text=True, timeout=10)
                bios_uuid = result.stdout.strip().split('\n')[-1].strip()
                if bios_uuid and bios_uuid != "UUID":
                    return bios_uuid
                    
            elif self.system == "Linux":
                # DMI/SMBIOS info
                paths = ['/sys/class/dmi/id/board_serial', '/sys/class/dmi/id/product_uuid']
                for path in paths:
                    try:
                        with open(path, 'r') as f:
                            data = f.read().strip()
                            if data and data not in ["", "To be filled by O.E.M."]:
                                return data
                    except:
                        continue
                        
            elif self.system == "Darwin":  # macOS
                result = self._run_subprocess_hidden(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if 'Hardware UUID' in line:
                        return line.split(':')[1].strip()
                        
        except Exception:
            pass
            
        return platform.node()  # Fallback to hostname
    
    def get_storage_info(self) -> str:
        """Lấy thông tin storage devices"""
        storage_ids = []
        
        try:
            if self.system == "Windows":
                # Lấy physical disk serials
                result = self._run_subprocess_hidden(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                      capture_output=True, text=True, timeout=10)
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    serial = line.strip()
                    if serial and serial not in ["SerialNumber", "(null)"]:
                        storage_ids.append(serial)
                        
            elif self.system == "Linux":
                # Lấy block device info
                try:
                    result = self._run_subprocess_hidden(['lsblk', '-o', 'SERIAL', '-n'], 
                                          capture_output=True, text=True, timeout=10)
                    for line in result.stdout.split('\n'):
                        serial = line.strip()
                        if serial and serial != "":
                            storage_ids.append(serial)
                except:
                    # Fallback: check /dev/disk/by-id
                    try:
                        disk_path = '/dev/disk/by-id'
                        if os.path.exists(disk_path):
                            for disk in os.listdir(disk_path):
                                if 'ata-' in disk or 'nvme-' in disk:
                                    storage_ids.append(disk)
                    except:
                        pass
                        
            elif self.system == "Darwin":  # macOS
                result = self._run_subprocess_hidden(['system_profiler', 'SPStorageDataType'], 
                                      capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if 'Device / Media Name' in line:
                        storage_ids.append(line.split(':')[1].strip())
                        
        except Exception:
            pass
            
        return "|".join(sorted(storage_ids)) if storage_ids else "unknown_storage"
    
    def get_network_info(self) -> str:
        """Lấy MAC addresses của network interfaces"""
        mac_addresses = []
        
        try:
            if self.system == "Windows":
                result = self._run_subprocess_hidden(['getmac', '/fo', 'csv', '/nh'], 
                                      capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if line.strip():
                        # Parse CSV output
                        parts = line.strip().split(',')
                        if len(parts) >= 1:
                            mac = parts[0].strip('"').replace('-', ':')
                            if mac and mac != "N/A":
                                mac_addresses.append(mac.lower())
                                
            else:  # Linux/macOS
                try:
                    import netifaces
                    for interface in netifaces.interfaces():
                        try:
                            addrs = netifaces.ifaddresses(interface)
                            if netifaces.AF_LINK in addrs:
                                for addr_info in addrs[netifaces.AF_LINK]:
                                    mac = addr_info.get('addr')
                                    if mac and mac != '00:00:00:00:00:00':
                                        mac_addresses.append(mac.lower())
                        except:
                            continue
                except ImportError:
                    # Fallback if netifaces not available
                    pass
                        
        except ImportError:
            # Fallback nếu không có netifaces
            try:
                # Dùng uuid.getnode() as fallback
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
                mac_addresses.append(mac.lower())
            except:
                pass
        except Exception:
            pass
            
        # Loại bỏ virtual interfaces
        filtered_macs = []
        for mac in mac_addresses:
            # Skip virtual/docker interfaces
            if not any(prefix in mac for prefix in ['02:42:', '00:15:5d:', '00:50:56:']):
                filtered_macs.append(mac)
                
        return "|".join(sorted(filtered_macs)) if filtered_macs else "unknown_mac"
    
    def get_system_info(self) -> str:
        """Lấy system-specific info"""
        info_parts = []
        
        try:
            # System UUID (Windows)
            if self.system == "Windows":
                result = self._run_subprocess_hidden(['wmic', 'csproduct', 'get', 'name'], 
                                      capture_output=True, text=True, timeout=10)
                product_name = result.stdout.strip().split('\n')[-1].strip()
                if product_name and product_name != "Name":
                    info_parts.append(product_name)
            
            # Boot ID (Linux)
            elif self.system == "Linux":
                try:
                    with open('/proc/sys/kernel/random/boot_id', 'r') as f:
                        boot_id = f.read().strip()
                        info_parts.append(boot_id)
                except:
                    pass
                    
            # System info for all platforms
            info_parts.extend([
                platform.system(),
                platform.release(),
                platform.version()[:50]  # Limit length
            ])
            
        except Exception:
            pass
            
        return "|".join(info_parts)
    
    def collect_fingerprint_data(self) -> Dict[str, str]:
        """Thu thập tất cả fingerprint data"""
        self.fingerprint_data = {
            'cpu': self.get_cpu_info(),
            'motherboard': self.get_motherboard_info(),
            'storage': self.get_storage_info(),
            'network': self.get_network_info(),
            'system': self.get_system_info(),
            'platform': f"{platform.system()}_{platform.machine()}_{platform.architecture()[0]}"
        }
        
        return self.fingerprint_data
    
    def generate_device_id(self, include_volatile: bool = False) -> str:
        """
        Tạo device ID từ hardware fingerprint
        
        Args:
            include_volatile: Có bao gồm thông tin có thể thay đổi (IP, hostname) không
        """
        # Thu thập fingerprint data
        data = self.collect_fingerprint_data()
        
        # Tạo stable hash từ hardware components
        stable_components = [
            data.get('cpu', ''),
            data.get('motherboard', ''),
            data.get('storage', ''),
            data.get('network', ''),
            data.get('platform', '')
        ]
        
        if include_volatile:
            # Thêm hostname và user info
            stable_components.extend([
                platform.node(),
                os.environ.get('USERNAME', os.environ.get('USER', ''))
            ])
        
        # Combine và hash
        combined = "|".join(filter(None, stable_components))
        
        # Tạo SHA-256 hash
        device_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        # Format như UUID để dễ đọc
        formatted_id = f"{device_hash[:8]}-{device_hash[8:12]}-{device_hash[12:16]}-{device_hash[16:20]}-{device_hash[20:32]}"
        
        return formatted_id
    
    def get_device_info_summary(self) -> Dict[str, str]:
        """Lấy thông tin tóm tắt về device (for debugging)"""
        if not self.fingerprint_data:
            self.collect_fingerprint_data()
            
        return {
            'device_id': self.generate_device_id(),
            'system': self.system,
            'cpu_info': self.fingerprint_data.get('cpu', 'Unknown')[:50],
            'motherboard': self.fingerprint_data.get('motherboard', 'Unknown')[:50],
            'network_count': len(self.fingerprint_data.get('network', '').split('|')),
            'storage_count': len(self.fingerprint_data.get('storage', '').split('|'))
        }
    
    def validate_device_change(self, stored_device_id: str) -> Dict[str, any]:
        """
        Kiểm tra xem device có thay đổi không
        Trả về thông tin chi tiết về sự thay đổi
        """
        current_id = self.generate_device_id()
        
        result = {
            'is_same_device': current_id == stored_device_id,
            'current_id': current_id,
            'stored_id': stored_device_id,
            'confidence': 0.0,
            'changes': []
        }
        
        if result['is_same_device']:
            result['confidence'] = 1.0
            return result
        
        # Phân tích chi tiết sự khác biệt
        current_data = self.collect_fingerprint_data()
        
        # Tính confidence score dựa trên số components giống nhau
        # (Cần stored fingerprint data để so sánh chính xác)
        # Ở đây chỉ là estimation
        
        # Nếu chỉ network thay đổi => vẫn có thể same device
        network_only_change = True
        for key, value in current_data.items():
            if key != 'network' and value != stored_device_id:
                network_only_change = False
                break
        
        if network_only_change:
            result['confidence'] = 0.8
            result['changes'].append('network_interface_change')
        else:
            result['confidence'] = 0.2
            result['changes'].append('hardware_change')
        
        return result


def get_device_fingerprint() -> str:
    """
    Convenience function để lấy device fingerprint
    """
    fingerprinter = DeviceFingerprint()
    return fingerprinter.generate_device_id()


def get_device_info() -> Dict[str, str]:
    """
    Convenience function để lấy device info summary
    """
    fingerprinter = DeviceFingerprint()
    return fingerprinter.get_device_info_summary()


# Test function
if __name__ == "__main__":
    fingerprinter = DeviceFingerprint()
    
    print("=== Device Fingerprint Test ===")
    device_id = fingerprinter.generate_device_id()
    print(f"Device ID: {device_id}")
    
    print("\n=== Device Info Summary ===")
    info = fingerprinter.get_device_info_summary()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("\n=== Raw Fingerprint Data ===")
    data = fingerprinter.collect_fingerprint_data()
    for key, value in data.items():
        print(f"{key}: {value[:100]}{'...' if len(value) > 100 else ''}") 