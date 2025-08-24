import logging
import random
import time
import os
import datetime
import json
import pickle
import base64
import math
import warnings
from io import BytesIO
import sys

# 抑制警告信息
warnings.filterwarnings("ignore")

# 抑制Selenium的一些警告
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 全局配置
ARTICLE_READ_TIME = 70  # 阅读文章时间(秒)
VIDEO_WATCH_TIME = 180  # 观看视频时间(秒)
WAIT_TIMEOUT = 30  # 等待元素超时时间(秒)
EDGE_DRIVER_PATH = None  # 可以手动指定Edge驱动路径


class XueXiQiangGuoAssistant:
    """学习强国助手类"""
    
    def __init__(self):
        self.driver = None
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('XueXiQiangGuoAssistant')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_edge_driver_path(self):
        """获取Edge驱动路径，支持离线模式"""
        try:
            # 尝试自动下载（在线模式）
            try:
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                return EdgeChromiumDriverManager(
                    url="https://msedgedriver.microsoft.com/",
                    latest_release_url="https://msedgedriver.microsoft.com/LATEST_RELEASE"
                ).install()
            except ImportError:
                self.logger.warning("webdriver_manager 未安装，尝试使用系统路径中的驱动")
            except Exception as e:
                self.logger.warning(f"自动下载驱动失败: {e}")
            
            # 离线模式：检查常见路径
            possible_paths = [
                EDGE_DRIVER_PATH,
                "msedgedriver",  # 当前目录
                "/usr/local/bin/msedgedriver",  # Linux
                "/usr/bin/msedgedriver",  # Linux
                "C:\\Program Files\\EdgeDriver\\msedgedriver.exe",  # Windows
                "C:\\Windows\\System32\\msedgedriver.exe",  # Windows
            ]
            
            for path in possible_paths:
                if path and os.path.exists(path):
                    self.logger.info(f"使用Edge驱动: {path}")
                    return path
            
            # 如果都没找到，提示用户手动指定
            self.logger.error("未找到Edge驱动，请手动安装并指定路径")
            manual_path = input("请输入Edge驱动的完整路径（或按Enter退出）: ").strip()
            if manual_path and os.path.exists(manual_path):
                return manual_path
            else:
                raise Exception("未找到有效的Edge驱动路径")
                
        except Exception as e:
            self.logger.error(f"获取Edge驱动路径失败: {e}")
            return None
    
    def initialize_driver(self):
        """初始化WebDriver，支持离线模式"""
        try:
            # 设置Edge选项
            edge_options = Options()
            
            # GPU和WebGL相关选项
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--disable-gpu-sandbox")
            edge_options.add_argument("--disable-software-rasterizer")
            edge_options.add_argument("--disable-webgl")
            edge_options.add_argument("--disable-webgl2")
            edge_options.add_argument("--disable-3d-apis")
            edge_options.add_argument("--disable-accelerated-2d-canvas")
            edge_options.add_argument("--disable-accelerated-video-decode")
            
            # 安全和性能选项
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-extensions")
            edge_options.add_argument("--disable-plugins")
            edge_options.add_argument("--disable-images")
            edge_options.add_argument("--disable-javascript-harmony-shipping")
            
            # 窗口和显示选项
            edge_options.add_argument("--window-size=1920,1080")
            edge_options.add_argument("--disable-web-security")
            edge_options.add_argument("--allow-running-insecure-content")
            
            # 日志级别设置（减少错误信息输出）
            edge_options.add_argument("--log-level=3")
            edge_options.add_argument("--silent")
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            edge_options.add_experimental_option('useAutomationExtension', False)
            
            # 可选：取消注释以下行以启用无头模式
            edge_options.add_argument("--headless")
            
            # 获取驱动路径
            driver_path = self._get_edge_driver_path()
            if not driver_path:
                return False

            # 初始化WebDriver
            self.logger.info("正在初始化浏览器...")
            service = Service(executable_path=driver_path)
            self.driver = webdriver.Edge(service=service, options=edge_options)
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)
            
            self.logger.info("浏览器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化WebDriver时发生错误: {e}")
            return False
    
    def check_network_connection(self):
        """检查网络连接状态"""
        try:
            import socket
            socket.create_connection(("www.baidu.com", 80), timeout=5)
            self.logger.info("网络连接正常")
            return True
        except OSError:
            self.logger.warning("网络连接异常，请检查网络设置")
            return False
    
    def extract_login_qrcode(self, output_path=None):
        """
        提取学习强国登录页面的二维码图片并保存到文件
        """
        if not self.driver:
            self.logger.error("浏览器未初始化，请先调用 initialize_driver()")
            return None
            
        try:
            if output_path is None:
                output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_qrcode.png")
            
            # 确保页面已加载到登录页
            if "login.html" not in self.driver.current_url:
                self.logger.info("正在跳转到登录页面...")
                self.driver.get("https://pc.xuexi.cn/points/login.html")
                time.sleep(3)
            
            # 切换到登录iframe
            wait = WebDriverWait(self.driver, WAIT_TIMEOUT)
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ddlogin-iframe")))
            self.logger.info("已切换到登录iframe")
            
            # 查找二维码图片元素
            try:
                # 尝试多种可能的选择器
                qr_selectors = [
                    '//*[@id="app"]/div/div[1]/div/div[1]/div[1]/img',
                    '//img[contains(@src, "base64")]',
                    '//div[contains(@class, "qrcode")]//img'
                ]
                
                qr_element = None
                for selector in qr_selectors:
                    try:
                        qr_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                        if qr_element:
                            break
                    except:
                        continue
                
                if not qr_element:
                    self.logger.error("未找到二维码元素")
                    return None
                
                # 获取图片元素的src属性
                src = qr_element.get_attribute('src')
                
                if src and 'base64,' in src:
                    base64_data = src.split('base64,')[1]
                    img_data = base64.b64decode(base64_data)
                    img = Image.open(BytesIO(img_data))
                    img.save(output_path)
                    
                    if os.path.exists(output_path):
                        self.logger.info(f"二维码已保存到: {output_path}")
                        return output_path
                else:
                    self.logger.warning("图片元素不包含base64编码的数据")
                    
            except Exception as e:
                self.logger.error(f"提取二维码时出错: {e}")
                
            finally:
                self.driver.switch_to.default_content()
            
        except Exception as e:
            self.logger.error(f"提取二维码时发生错误: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
        
        return None

    def check_login_status(self):
        """通过cookie检测登录状态"""
        if not self.driver:
            self.logger.error("浏览器未初始化，请先调用 initialize_driver()")
            return False
            
        try:
            # 确保在xuexi.cn域名下
            current_url = self.driver.current_url
            if "xuexi.cn" not in current_url:
                # 导航到学习强国主页来检查cookie
                self.driver.get("https://www.xuexi.cn")
                time.sleep(2)
            
            # 获取xuexi.cn域名下的所有cookie
            cookies = self.driver.get_cookies()
            
            # 检查是否存在token相关的cookie
            token_found = False
            for cookie in cookies:
                cookie_name = cookie.get('name', '').lower()
                cookie_value = cookie.get('value', '')
                
                # 检查常见的token cookie名称
                if any(token_key in cookie_name for token_key in ['token', 'access_token', 'auth', 'session', 'login']):
                    if cookie_value and len(cookie_value) > 10:  # token通常比较长
                        self.logger.info(f"发现有效token: {cookie_name}")
                        token_found = True
                        break
            
            if token_found:
                # 进一步验证：尝试访问需要登录的页面
                try:
                    self.driver.get("https://pc.xuexi.cn/points/my-points.html")
                    time.sleep(3)
                    
                    # 检查是否被重定向到登录页面
                    current_url = self.driver.current_url
                    if "login.html" in current_url:
                        self.logger.info("虽然有token但被重定向到登录页，token可能已过期")
                        return False
                    
                    self.logger.info("通过cookie验证登录成功")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"验证登录状态时发生错误: {e}")
                    return False
            else:
                self.logger.info("未找到有效的登录token")
                return False
                
        except Exception as e:
            self.logger.error(f"检查登录状态时出错: {e}")
            return False

    def wait_for_login(self):
        """等待用户登录成功"""
        try:
            self.logger.info("请使用学习强国APP扫描二维码登录...")
            self.logger.info("等待登录成功...")
            
            timeout = 300  # 5分钟超时
            wait_end_time = time.time() + timeout
            check_count = 0

            while time.time() < wait_end_time:
                # 使用更严格的登录状态检查
                if self.check_login_status():
                    self.logger.info("登录验证成功！")
                    return True

                # 每10秒检查一次
                time.sleep(10)
                check_count += 1

                # 每30秒提醒一次
                if check_count % 3 == 0:
                    self.logger.info("仍在等待登录...如果已登录成功，请输入 'y' 确认")
                    user_input = input("已登录成功？(y/n): ").lower().strip()
                    if user_input == 'y':
                        # 用户确认后也要验证登录状态
                        if self.check_login_status():
                            self.logger.info("用户确认并验证登录成功！")
                            return True
                        else:
                            self.logger.warning("用户确认登录，但验证失败，请重新登录")

            # 超时处理
            self.logger.warning("登录等待超时")
            user_input = input("是否已成功登录？(y/n): ").lower().strip()
            if user_input == 'y':
                # 最后验证一次
                if self.check_login_status():
                    return True
                else:
                    self.logger.error("登录验证失败，请重新登录")
                    return False
            return False

        except Exception as e:
            self.logger.error(f"检测登录状态时出错: {e}")
            user_input = input("登录状态检测出错，是否已成功登录？(y/n): ").lower().strip()
            if user_input == 'y':
                return self.check_login_status()
            return False

    def launch_xuexi_website(self):
        """启动学习强国网站"""
        try:
            # 检查网络连接
            if not self.check_network_connection():
                self.logger.warning("继续尝试，但网络可能不稳定...")
            
            # 初始化浏览器
            if not self.initialize_driver():
                return

            # 打开学习强国登录页面
            self.logger.info("正在打开学习强国...")
            self.driver.get("https://www.xuexi.cn")
            time.sleep(3)
            
            # 检查是否已经登录（使用更严格的检查）
            if self.check_login_status():
                self.logger.info("检测到已登录状态，直接进入学习页面")
                self.show_menu()
                return

            # 未登录，跳转到登录页面
            self.logger.info("未检测到登录状态，跳转到登录页面")
            self.driver.get("https://pc.xuexi.cn/points/login.html")
            time.sleep(3)

            # 提取并显示二维码
            qr_path = self.extract_login_qrcode()
            if qr_path:
                try:
                    img = Image.open(qr_path)
                    img.show()
                    self.logger.info("二维码已显示，请使用学习强国APP扫描")
                except:
                    self.logger.info(f"无法自动显示图片，请手动查看: {qr_path}")
            
            # 等待登录
            if self.wait_for_login():
                # 清理二维码文件
                if qr_path and os.path.exists(qr_path):
                    os.remove(qr_path)
                self.show_menu()
            else:
                self.logger.error("登录失败或超时")

        except Exception as e:
            self.logger.error(f"启动学习强国时发生错误: {e}")
        finally:
            self.quit_driver()
    
    def read_articles(self, num_articles=6, start_index=0):
        """
        阅读文章获取积分

        参数：
            num_articles: 要阅读的文章数量
            start_index: 从文章列表的第几篇文章开始阅读
        """
        if not self.driver:
            self.logger.error("浏览器未初始化，请先调用 initialize_driver()")
            return False
            
        try:
            # 跳转到新闻页面
            self.logger.info("正在跳转到新闻页面...")
            self.driver.get("https://www.xuexi.cn")
            
            time.sleep(2)

            # 等待文章列表加载
            article_links = WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='text-link-item-title']"))
            )

            # 阅读指定数量的文章
            read_count = min(len(article_links), num_articles)
            self.logger.info(f"找到{len(article_links)}篇文章，计划阅读{read_count}篇，从第{start_index + 1}篇开始")

            for i in range(read_count):
                # 重新获取文章列表，避免StaleElementReferenceException
                article_links = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@class='text-link-item-title']"))
                )

                # 计算实际的文章索引，使用模运算确保不会超出范围
                actual_index = (i + start_index) % len(article_links)
                self.logger.info(f"正在阅读第 {actual_index + 1}/{len(article_links)} 篇文章")

                # 点击对应索引的文章
                article_links[actual_index].click()

                # 切换到新窗口
                self.driver.switch_to.window(self.driver.window_handles[-1])

                # 模拟阅读行为，随机滚动页面
                read_time = 70 + random.randint(-10, 10)  # 阅读文章时间(秒)
                self.logger.info(f"阅读时间：{read_time}秒")

                end_time = time.time() + read_time
                while time.time() < end_time:
                    # 随机滚动页面
                    scroll_height = random.randint(100, 500)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                    time.sleep(random.uniform(2, 5))

                # 关闭当前文章窗口，回到文章列表
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                time.sleep(1)

            self.logger.info("文章阅读完成！")
            return True
        except Exception as e:
            self.logger.error(f"阅读文章时发生错误: {e}")
            return False
    
    def watch_videos(self, num_videos=6, start_index=0):
        """
        观看视频获取积分

        参数：
            num_videos: 要观看的视频数量
            start_index: 从视频列表的第几个视频开始观看
        """
        if not self.driver:
            self.logger.error("浏览器未初始化，请先调用 initialize_driver()")
            return False
            
        try:
            # 跳转到视频页面
            self.logger.info("正在跳转到视频页面...")
            self.driver.get("https://www.xuexi.cn/4426aa87b0b64ac671c96379a3a8bd26/db086044562a57b441c24f2af1c8e101.html")
            
            time.sleep(3)

            # 等待视频列表加载 - 调整选择器以匹配视频列表项
            self.logger.info("等待视频列表加载...")

            # 尝试多种选择器
            selector_options = [
                {"type": "xpath", "value": "//div[contains(@class, 'thePic')][@data-link-target]"},
                {"type": "xpath", "value": "//div[contains(@class, 'textWrapper')][@data-link-target]"},
                {"type": "xpath", "value": "//div[contains(@class, 'grid-cell')]//div[contains(@class, 'innerPic')]"},
                {"type": "css", "value": ".grid-gr .grid-cell"}
            ]

            # 尝试每个选择器
            current_selector = None
            for selector in selector_options:
                try:
                    if selector["type"] == "xpath":
                        video_links = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_all_elements_located((By.XPATH, selector["value"]))
                        )
                    else:
                        video_links = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector["value"]))
                        )

                    if video_links and len(video_links) > 0:
                        self.logger.info(f"找到 {len(video_links)} 个视频，使用选择器: {selector['value']}")
                        current_selector = selector  # 保存成功的选择器
                        break
                except Exception as e:
                    self.logger.debug(f"选择器 {selector['value']} 未找到元素")

            if not current_selector:
                self.logger.error("无法找到视频列表，任务无法完成")
                return False

            # 观看指定数量的视频
            watch_count = min(len(video_links), num_videos)
            self.logger.info(f"计划观看{watch_count}个视频，从第{start_index + 1}个开始")

            for i in range(watch_count):
                # 重新获取视频列表，使用成功的选择器
                try:
                    if current_selector["type"] == "xpath":
                        video_links = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_all_elements_located((By.XPATH, current_selector["value"]))
                        )
                    else:
                        video_links = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, current_selector["value"]))
                        )

                    # 计算实际的视频索引，使用模运算确保不会超出范围
                    actual_index = (i + start_index) % len(video_links)
                    self.logger.info(f"正在观看第 {actual_index + 1}/{len(video_links)} 个视频")

                    # 确保元素可点击
                    try:
                        if current_selector["type"] == "xpath":
                            WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, current_selector["value"]))
                            )
                        else:
                            WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, current_selector["value"]))
                            )
                    except Exception as e:
                        self.logger.debug(f"等待元素可点击时出错: {e}")

                    # 使用JavaScript点击元素
                    try:
                        self.driver.execute_script("arguments[0].click();", video_links[actual_index])
                    except Exception as e:
                        self.logger.warning(f"点击视频时出错，尝试替代方法: {e}")
                        try:
                            video_links[actual_index].click()
                        except:
                            self.logger.error("替代点击方法也失败，跳过此视频")
                            continue

                    # 切换到新窗口
                    try:
                        if len(self.driver.window_handles) > 1:
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                        else:
                            self.logger.info("没有新窗口打开，继续处理当前页面")
                    except Exception as e:
                        self.logger.error(f"切换窗口时出错: {e}")
                        continue

                    # 等待视频加载并播放
                    try:
                        # 尝试多个可能的视频选择器
                        video_selectors = ["//video", "//div[contains(@class,'outter')]//video", "//div[@id='ji-player']"]
                        video_player = None

                        for selector in video_selectors:
                            try:
                                video_player = WebDriverWait(self.driver, 30).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                if video_player:
                                    break
                            except:
                                continue

                        if video_player:
                            # 设置视频静音
                            self.driver.execute_script("arguments[0].muted = true;", video_player)
                            self.logger.info("已将视频设为静音模式")

                            # 确保视频开始播放
                            self.driver.execute_script("arguments[0].play();", video_player)
                            
                            # 等待视频加载并获取时长
                            video_duration = 0
                            wait_duration_time = time.time() + 10
                            while time.time() < wait_duration_time:
                                try:
                                    video_duration = self.driver.execute_script("return arguments[0].duration", video_player)
                                    if video_duration and video_duration > 0 and not math.isnan(video_duration):
                                        break
                                except:
                                    pass
                                time.sleep(1)
                            
                            # 根据视频时长决定观看时间
                            if video_duration and video_duration > 0:
                                minutes = int(video_duration // 60)
                                seconds = int(video_duration % 60)
                                self.logger.info(f"检测到视频时长: {minutes}分{seconds}秒 ({video_duration:.1f}秒)")
                                
                                watch_time = int(video_duration) + random.randint(5, 10)
                                
                                if watch_time > 300:  # 如果超过5分钟
                                    watch_time = 300    # 直接设置为5分钟
                            else:
                                self.logger.info("无法获取视频时长，使用默认观看时间")
                                watch_time = 180 + random.randint(-15, 15)
                            
                            # 检查视频是否真的在播放
                            is_playing = self.driver.execute_script(
                                "return arguments[0].paused === false && arguments[0].currentTime > 0",
                                video_player
                            )

                            if not is_playing:
                                self.logger.info("尝试手动开始播放视频")
                                play_buttons = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'play')]")
                                if play_buttons:
                                    play_buttons[0].click()
                    except Exception as e:
                        self.logger.error(f"播放视频时出错: {e}")
                        watch_time = 180 + random.randint(-15, 15)

                    self.logger.info(f"观看时间：{watch_time}秒")
                    
                    # 观看视频，并定期检查播放状态
                    end_time = time.time() + watch_time
                    while time.time() < end_time:
                        remaining_time = end_time - time.time()
                        
                        # 只在距离结束还有超过30秒时进行滚动
                        if remaining_time > 30:
                            scroll_height = random.randint(100, 400)
                            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                            
                            time.sleep(random.uniform(2, 5))
                            if random.random() > 0.5:  # 50%的概率滚回一些距离
                                back_scroll = random.randint(50, scroll_height)
                                self.driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
                        
                        # 每隔15-30秒检查一次视频是否仍在播放
                        check_interval = random.uniform(15, 30)
                        check_interval = min(check_interval, remaining_time)
                        time.sleep(check_interval)
                        
                        try:
                            if video_player:
                                is_paused = self.driver.execute_script("return arguments[0].paused", video_player)
                                if is_paused:
                                    self.logger.info("视频已暂停，尝试继续播放")
                                    self.driver.execute_script("arguments[0].play();", video_player)
                        except:
                            pass
                    
                    # 观看结束，确保视频在可见区域
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video_player)
                    except Exception as e:
                        self.logger.debug(f"滚动到视频位置失败: {e}")

                    # 关闭当前视频窗口，回到视频列表
                    try:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    except Exception as e:
                        self.logger.error(f"关闭视频窗口时出错: {e}")
                        if len(self.driver.window_handles) > 0:
                            self.driver.switch_to.window(self.driver.window_handles[0])
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"重新获取视频列表时出错: {e}")
                    continue

            self.logger.info("视频观看完成！")
            return True
        except Exception as e:
            self.logger.error(f"观看视频时发生错误: {e}")
            if len(self.driver.window_handles) > 0:
                self.driver.switch_to.window(self.driver.window_handles[0])
            return False
    
    def check_score(self, verbose=False):
        """
        查看当前学习积分，并返回文章和视频的积分状态
        verbose: 是否显示详细信息
        """
        if not self.driver:
            self.logger.error("浏览器未初始化，请先调用 initialize_driver()")
            return {
                'article': {'current': 0, 'target': 12},
                'video': {'current': 0, 'target': 12}
            }
            
        try:
            # 跳转到积分页面
            self.logger.info("正在检查积分状态...")
            self.driver.get("https://pc.xuexi.cn/points/my-points.html")
            
            time.sleep(3)

            # 等待积分数据加载
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "my-points-content"))
            )

            # 提取各项积分详情
            article_points = {'current': 0, 'target': 12}
            video_points = {'current': 0, 'target': 12}

            try:
                score_cards = self.driver.find_elements(By.CLASS_NAME, "my-points-card")

                if verbose:
                    self.logger.info(f"积分详情: 找到 {len(score_cards)} 个积分卡片")

                # 只有在详细模式下才打印所有卡片
                if verbose:
                    self.logger.info("所有积分卡片标题:")
                    for i, card in enumerate(score_cards):
                        try:
                            title = card.find_element(By.CLASS_NAME, "my-points-card-title").text
                            progress = card.find_element(By.CLASS_NAME, "my-points-card-text").text
                            self.logger.info(f"{i + 1}. {title}: {progress}")
                        except:
                            pass

                # 解析积分详情
                for card in score_cards:
                    try:
                        title = card.find_element(By.CLASS_NAME, "my-points-card-title").text
                        progress = card.find_element(By.CLASS_NAME, "my-points-card-text").text

                        # 提取文章和视频的积分情况
                        if "选读文章" in title or "阅读文章" in title or "我要选读文章" in title:
                            try:
                                current, target = progress.split("/")
                                # 移除非数字字符再转换
                                current_clean = ''.join(filter(str.isdigit, current))
                                target_clean = ''.join(filter(str.isdigit, target))

                                article_points['current'] = int(current_clean)
                                article_points['target'] = int(target_clean)
                            except Exception as e:
                                if verbose:
                                    self.logger.warning(f"解析文章积分失败: {progress}, 错误: {e}")
                        elif ("视听学习" in title or "视频" in title) and (
                                "时长" in title or "分钟" in title or "我要" in title):
                            try:
                                current, target = progress.split("/")
                                # 移除非数字字符再转换
                                current_clean = ''.join(filter(str.isdigit, current))
                                target_clean = ''.join(filter(str.isdigit, target))

                                video_points['current'] = int(current_clean)
                                video_points['target'] = int(target_clean)
                            except Exception as e:
                                if verbose:
                                    self.logger.warning(f"解析视频积分失败: {progress}, 错误: {e}")
                    except Exception as e:
                        if verbose:
                            self.logger.warning(f"获取积分卡片详情失败: {e}")

                # 简洁的积分汇总
                self.logger.info(f"积分进度: 文章 {article_points['current']}/{article_points['target']} | " +
                      f"视频 {video_points['current']}/{video_points['target']}")
            except Exception as e:
                if verbose:
                    self.logger.error(f"获取积分详情失败: {e}")

            return {
                'article': article_points,
                'video': video_points
            }
        except Exception as e:
            if verbose:
                self.logger.error(f"查看积分时发生错误: {e}")
            return {
                'article': {'current': 0, 'target': 12},
                'video': {'current': 0, 'target': 12}
            }
    
    def show_menu(self):
        """显示功能菜单并处理用户选择"""
        while True:
            print("\n=== 学习强国助手菜单 ===")
            print("1. 阅读文章（获取积分）")
            print("2. 观看视频（获取积分）")
            print("3. 查看我的积分")
            print("4. 阅读文章+观看视频（全自动）")
            print("0. 退出程序")

            choice = input("\n请选择功能 (0-4): ").strip()

            if choice == '1':
                num = input("请输入要阅读的文章数量 (默认12篇): ").strip()
                num = int(num) if num.isdigit() else 12
                self.read_articles(num)
            elif choice == '2':
                num = input("请输入要观看的视频数量 (默认12个): ").strip()
                num = int(num) if num.isdigit() else 12
                self.watch_videos(num)
            elif choice == '3':
                self.check_score(verbose=True)
            elif choice == '4':
                self.run_automatic_learning()
            elif choice == '0':
                self.logger.info("正在退出程序...")
                break
            else:
                print("无效选择，请重新输入")
    
    def run_automatic_learning(self):
        """全自动学习"""
        if not self.driver:
            self.logger.error("浏览器未初始化，请先调用 initialize_driver()")
            return False
            
        try:
            self.logger.info("===== 开始全自动学习 =====")

            # 初始化检查积分状态
            score_status = self.check_score(verbose=False)

            # 持续检查直到所有任务完成
            while True:
                # 计算所需的阅读文章和观看视频数量
                article_target = score_status['article']['target']
                article_current = score_status['article']['current']
                article_remaining = max(0, article_target - article_current)

                video_target = score_status['video']['target']
                video_current = score_status['video']['current']
                video_remaining = max(0, video_target - video_current)

                # 显示完成百分比
                article_percent = min(100, int(article_current / article_target * 100))
                video_percent = min(100, int(video_current / video_target * 100))
                self.logger.info(f"当前进度: 文章 {article_percent}% | 视频 {video_percent}%")

                # 如果两种任务都已完成，退出循环
                if article_remaining <= 0 and video_remaining <= 0:
                    self.logger.info("✅ 所有学习任务已完成！")
                    break

                # 自动完成文章阅读任务，从已阅读的文章数量开始
                if article_remaining > 0:
                    batch_articles = min(6, article_remaining)
                    # 传递已获得的文章积分作为起始索引
                    self.read_articles(batch_articles, article_current)

                # 简短地检查积分状态
                score_status = self.check_score(verbose=False)

                # 如果已完成所有任务，提前退出
                if score_status['article']['current'] >= article_target and score_status['video']['current'] >= video_target:
                    self.logger.info("✅ 所有学习任务已完成！")
                    break

                # 自动完成视频观看任务，从已观看的视频数量开始
                if video_remaining > 0:
                    batch_videos = min(6, video_remaining)
                    # 传递已获得的视频积分作为起始索引
                    self.watch_videos(batch_videos, video_current)

                # 再次检查积分状态
                score_status = self.check_score(verbose=False)
                
            return True
        except Exception as e:
            self.logger.error(f"全自动学习过程中发生错误: {e}")
            return False

    def quit_driver(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("浏览器已关闭")
            except:
                pass


def check_dependencies():
    """检查必要的依赖"""
    try:
        from PIL import Image
        from selenium import webdriver
        return True
    except ImportError as e:
        print(f"缺少必要依赖: {e}")
        print("请安装所需包: pip install selenium pillow")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("学习强国自动化助手")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 运行助手
    assistant = XueXiQiangGuoAssistant()
    assistant.launch_xuexi_website()


if __name__ == "__main__":
    main()
