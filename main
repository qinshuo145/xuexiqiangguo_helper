import random
import time
import os
import datetime
import json
import pickle
import base64
from io import BytesIO
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 全局配置
ARTICLE_READ_TIME = 70  # 阅读文章时间(秒)
VIDEO_WATCH_TIME = 180  # 观看视频时间(秒)
WAIT_TIMEOUT = 30  # 等待元素超时时间(秒)

def extract_login_qrcode(driver, output_path=None):
    """
    提取学习强国登录页面的二维码图片并保存到文件
    
    参数：
        driver: WebDriver实例
        output_path: 保存图片的路径，默认为脚本所在目录的login_qrcode.png
    
    返回：
        保存的图片路径或None（如果提取失败）
    """
    try:
        # 如果未提供文件路径，使用默认路径
        if output_path is None:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_qrcode.png")
        
        # 确保页面已加载到登录页
        if "login.html" not in driver.current_url:
            print("正在跳转到登录页面...")
            driver.get("https://pc.xuexi.cn/points/login.html")
            time.sleep(2)
        
        # 切换到登录iframe
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ddlogin-iframe")))
        print("已切换到ddlogin-iframe")
        
        # 查找二维码图片元素
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/div[1]/div/div[1]/div[1]/img')))
            #print("找到二维码元素")
            
            # 获取图片元素的src属性
            src = element.get_attribute('src')
            #print(f"图片src属性长度: {len(src) if src else 0}")
            
            # 提取base64编码部分
            if src and 'base64,' in src:
                # 分割字符串，获取base64编码部分
                base64_data = src.split('base64,')[1]
                #print(f"成功提取base64编码，长度: {len(base64_data)}")
                
                # 解码base64数据
                img_data = base64.b64decode(base64_data)
                
                # 使用PIL处理图片
                img = Image.open(BytesIO(img_data))
                #print(f"图片尺寸: {img.size}")
                
                # 保存图片
                img.save(output_path)
                #print(f"二维码已保存至: {output_path}")

                
                # 验证文件是否存在
                if os.path.exists(output_path):
                    #print("图片文件保存成功并且可以访问")
                    return output_path
            else:
                print("图片元素不包含base64编码的数据")
                
        except Exception as e:
            print(f"在ddlogin-iframe中找不到目标元素或处理图片时出错: {e}")
            import traceback
            print(traceback.format_exc())
            
        # 操作完成后，切换回默认内容
        driver.switch_to.default_content()
        
    except Exception as e:
        print(f"提取二维码时发生错误: {e}")
        import traceback
        print(traceback.format_exc())
        # 尝试切换回默认内容
        try:
            driver.switch_to.default_content()
        except:
            pass
    
    return None

def save_cookies(driver, filename='xuexi_cookies.pkl'):
    """
    保存当前浏览器会话的cookies到文件
    """
    # 创建存储目录
    os.makedirs(os.path.dirname(os.path.abspath(filename)) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # 获取所有cookies
    cookies = driver.get_cookies()
    
    # 保存到文件
    with open(filename, 'wb') as f:
        pickle.dump(cookies, f)
    
    print(f"已保存登录状态到 {filename}")
    
    # 同时保存cookie信息和时间戳
    cookie_info = {
        'save_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cookie_count': len(cookies),
        'domains': list(set(cookie.get('domain', 'unknown') for cookie in cookies if 'domain' in cookie))
    }
    
    with open(f"{filename}.json", 'w', encoding='utf-8') as f:
        json.dump(cookie_info, f, ensure_ascii=False, indent=2)

def load_cookies(driver, filename='xuexi_cookies.pkl', max_age_days=7):
    """
    从文件加载cookies到当前浏览器会话
    返回是否成功加载cookies
    """
    # 检查cookie文件是否存在
    if not os.path.exists(filename):
        print("未找到已保存的登录状态")
        return False
    
    # 检查cookie是否过期
    try:
        # 获取文件修改时间
        file_time = os.path.getmtime(filename)
        file_age = (time.time() - file_time) / 86400  # 转换为天
        
        if file_age > max_age_days:
            print(f"已保存的登录状态已过期 ({int(file_age)}天前保存)")
            return False
            
        # 加载cookies
        with open(filename, 'rb') as f:
            cookies = pickle.load(f)
        
        # 按域名分组cookies
        cookies_by_domain = {}
        for cookie in cookies:
            domain = cookie.get('domain', '')
            if domain not in cookies_by_domain:
                cookies_by_domain[domain] = []
            cookies_by_domain[domain].append(cookie)
        
        # 先访问学习强国主域名
        driver.get("https://www.xuexi.cn")
        time.sleep(1)
        
        # 按域名添加cookies
        success_count = 0
        for domain, domain_cookies in cookies_by_domain.items():
            # 尝试访问与cookie域名匹配的页面
            try:
                # 提取域名的主要部分并访问
                base_domain = domain.lstrip('.')
                if base_domain and '.' in base_domain:  # 确保是有效域名
                    protocol = "https://" if not base_domain.startswith("http") else ""
                    # 构建URL并访问该域
                    url = f"{protocol}{base_domain}"
                    #print(f"访问域名 {url} 以设置相关cookie...")
                    driver.get(url)
                    time.sleep(1)
                
                # 添加该域的cookies
                for cookie in domain_cookies:
                    try:
                        # 修复可能的cookie格式问题
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        
                        # 确保domain与当前页面匹配
                        current_domain = driver.current_url.split('//')[1].split('/')[0]
                        if domain.endswith(current_domain) or current_domain.endswith(domain.lstrip('.')):
                            driver.add_cookie(cookie)
                            success_count += 1
                        else:
                            print(f"跳过不匹配的cookie: {cookie.get('name')} (域名: {domain} vs 当前: {current_domain})")
                    except Exception as e:
                        print(f"添加cookie时出错 [{cookie.get('name')}]: {str(e).split('Stacktrace')[0].strip()}")
            except Exception as e:
                print(f"访问域名 {domain} 时出错: {e}")
        
        # 重新访问学习强国主页
        driver.get("https://www.xuexi.cn")
        time.sleep(2)
        
        # 验证登录状态
        current_url = driver.current_url
        if "login.html" in current_url:
            print("使用已保存的登录状态失败")
            return False
        
        #print(f"已成功添加 {success_count}/{len(cookies)} 个cookies，自动登录成功！")
        return True
        
    except Exception as e:
        print(f"加载登录状态时出错: {e}")
        return False

def wait_for_login(driver):
    """
    等待用户登录成功
    """
    try:
        print("等待登录成功...")
        # 尝试二维码登录

        # 设置较长的等待时间给用户登录
        timeout = 300
        wait_end_time = time.time() + timeout

        # 登录检测循环
        while time.time() < wait_end_time:
            # 检查URL变化
            current_url = driver.current_url
            if "login.html" not in current_url:
                print("登录成功！")
                return True

            # 每5秒检查一次
            time.sleep(5)

            # 每30秒询问用户是否已登录成功
            if int(time.time() - (wait_end_time - timeout)) % 30 < 5:
                user_confirm = input("自动检测登录状态中... 如果你已登录成功，请输入'y'确认，或按Enter继续等待: ")
                if user_confirm.lower() == 'y':
                    print("用户确认已登录成功！")
                    return True

        # 超时后，最后一次询问用户
        user_confirm = input("登录等待超时。如果你已经成功登录，请输入'y'确认继续，否则程序将退出: ")
        if user_confirm.lower() == 'y':
            print("用户确认已登录成功！")
            return True
        else:
            print("登录失败，程序退出")
            return False

    except Exception as e:
        print(f"检测登录状态时出错: {e}")
        # 出错后让用户决定是否继续
        user_confirm = input("登录状态检测出错。如果你确认已登录成功，请输入'y'继续，否则程序将退出: ")
        return user_confirm.lower() == 'y'

def launch_xuexi_website():
    """
    启动学习强国网站登录页面
    """
    try:
        # 设置Edge选项
        edge_options = Options()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-extensions")
        
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)

        # 尝试使用已保存的cookies登录
        login_success = load_cookies(driver)
        
        # 如果自动登录失败，则转向正常登录流程
        if not login_success:
            # 打开学习强国登录页面
            print("正在打开学习强国登录页面...")
            driver.get("https://pc.xuexi.cn/points/login.html")

            print("页面已打开，请扫描二维码登录...")
            output_path=extract_login_qrcode(driver)
            img = Image.open(output_path)
            img.show()
            # 等待用户登录成功
            if wait_for_login(driver):
                # 登录成功后保存cookies
                save_cookies(driver)
                os.remove(output_path)
            else:
                print("登录失败")
                driver.quit()
                return

        # 显示功能菜单并处理用户选择
        show_menu(driver)

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭浏览器
        if 'driver' in locals():
            driver.quit()
            print("浏览器已关闭")

def read_articles(driver, num_articles=6):
    """
    阅读文章获取积分
    """
    try:
        # 跳转到新闻页面
        print("正在跳转到新闻页面...")
        driver.get("https://www.xuexi.cn")
        time.sleep(2)

        # 等待文章列表加载
        article_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='text-link-item-title']"))
        )

        # 阅读指定数量的文章
        read_count = min(len(article_links), num_articles)
        print(f"找到{len(article_links)}篇文章，计划阅读{read_count}篇")

        for i in range(read_count):
            # 重新获取文章列表，避免StaleElementReferenceException
            article_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='text-link-item-title']"))
            )

            print(f"正在阅读第 {i+1}/{read_count} 篇文章")
            article_links[i].click()

            # 切换到新窗口
            driver.switch_to.window(driver.window_handles[-1])

            # 模拟阅读行为，随机滚动页面
            read_time = ARTICLE_READ_TIME + random.randint(-10, 10)
            print(f"阅读时间：{read_time}秒")

            end_time = time.time() + read_time
            while time.time() < end_time:
                # 随机滚动页面
                scroll_height = random.randint(100, 500)
                driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                time.sleep(random.uniform(2, 5))

            # 关闭当前文章窗口，回到文章列表
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

        print("文章阅读完成！")
        return True
    except Exception as e:
        print(f"阅读文章时发生错误: {e}")
        return False

def watch_videos(driver, num_videos=6):
    """
    观看视频获取积分
    """
    try:
        # 跳转到视频页面 - 使用百灵视频页面
        print("正在跳转到视频页面...")
        driver.get("https://www.xuexi.cn/4426aa87b0b64ac671c96379a3a8bd26/db086044562a57b441c24f2af1c8e101.html")
        time.sleep(3)

        # 等待视频列表加载 - 调整选择器以匹配视频列表项
        print("等待视频列表加载...")
        
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
                    video_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector["value"]))
                    )
                else:
                    video_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector["value"]))
                    )
                    
                if video_links and len(video_links) > 0:
                    print(f"找到 {len(video_links)} 个视频，使用选择器: {selector['value']}")
                    current_selector = selector  # 保存成功的选择器
                    break
            except Exception as e:
                print(f"选择器 {selector['value']} 未找到元素")
        
        if not current_selector:
            print("无法找到视频列表，任务无法完成")
            return False

        # 观看指定数量的视频
        watch_count = min(len(video_links), num_videos)
        print(f"找到{len(video_links)}个视频，计划观看{watch_count}个")

        for i in range(watch_count):
            # 重新获取视频列表，使用成功的选择器
            try:
                if current_selector["type"] == "xpath":
                    video_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
                        EC.presence_of_all_elements_located((By.XPATH, current_selector["value"]))
                    )
                else:
                    video_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, current_selector["value"]))
                    )
                
                print(f"正在观看第 {i+1}/{watch_count} 个视频")
                
                # 确保元素可点击，使用当前选择器
                try:
                    if current_selector["type"] == "xpath":
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, current_selector["value"]))
                        )
                    else:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, current_selector["value"]))
                        )
                except Exception as e:
                    print(f"等待元素可点击时出错: {e}")
                
                # 使用JavaScript点击元素可能更可靠
                try:
                    driver.execute_script("arguments[0].click();", video_links[i])
                except Exception as e:
                    print(f"点击视频时出错，尝试替代方法: {e}")
                    try:
                        video_links[i].click()
                    except:
                        print("替代点击方法也失败，跳过此视频")
                        continue

                # 切换到新窗口
                try:
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                    else:
                        print("没有新窗口打开，继续处理当前页面")
                except Exception as e:
                    print(f"切换窗口时出错: {e}")
                    continue

                # 等待视频加载并播放
                try:
                    # 改进视频播放检测代码
                    try:
                        # 尝试多个可能的视频选择器
                        video_selectors = ["//video", "//div[contains(@class,'outter')]//video", "//div[@id='ji-player']"]
                        video_player = None

                        for selector in video_selectors:
                            try:
                                video_player = WebDriverWait(driver, WAIT_TIMEOUT).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                if video_player:
                                    break
                            except:
                                continue

                        if video_player:
                            # 设置视频静音
                            driver.execute_script("arguments[0].muted = true;", video_player)
                            print("已将视频设为静音模式")
                            
                            # 确保视频开始播放
                            driver.execute_script("arguments[0].play();", video_player)

                            # 检查视频是否真的在播放
                            is_playing = driver.execute_script(
                                "return arguments[0].paused === false && arguments[0].currentTime > 0", 
                                video_player
                            )

                            if not is_playing:
                                print("视频未成功播放，尝试其他方法...")
                                # 尝试点击播放按钮
                                play_buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'play')]")
                                if play_buttons:
                                    play_buttons[0].click()
                    except Exception as e:
                        print(f"播放视频时出错: {e}")

                    # 观看视频
                    watch_time = VIDEO_WATCH_TIME + random.randint(-15, 15)
                    print(f"观看时间：{watch_time}秒")
                    time.sleep(watch_time)
                except Exception as e:
                    print(f"播放视频时出错: {e}")

                # 关闭当前视频窗口，回到视频列表
                try:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                except Exception as e:
                    print(f"关闭视频窗口时出错: {e}")
                    # 尝试恢复到主窗口
                    if len(driver.window_handles) > 0:
                        driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
            except Exception as e:
                print(f"重新获取视频列表时出错: {e}")
                continue

        print("视频观看完成！")
        return True
    except Exception as e:
        print(f"观看视频时发生错误: {e}")
        # 尝试恢复会话
        if len(driver.window_handles) > 0:
            driver.switch_to.window(driver.window_handles[0])
        return False

def check_score(driver):
    """
    查看当前学习积分
    """
    try:
        # 跳转到积分页面
        print("正在查询学习积分...")
        driver.get("https://pc.xuexi.cn/points/my-points.html")
        time.sleep(3)

        # 等待积分元素加载
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='my-points-block']"))
        )

        print("积分情况已加载，请查看浏览器窗口")
        input("按Enter键继续...")
        return True
    except Exception as e:
        print(f"查询积分时发生错误: {e}")
        return False


def show_menu(driver):
    """
    显示功能菜单并处理用户选择
    """
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
            read_articles(driver, num)
        elif choice == '2':
            num = input("请输入要观看的视频数量 (默认12个): ").strip()
            num = int(num) if num.isdigit() else 12
            watch_videos(driver, num)
        elif choice == '3':
            check_score(driver)
        elif choice == '4':
            num_articles = input("请输入要阅读的文章数量 (默认12篇): ").strip()
            num_articles = int(num_articles) if num_articles.isdigit() else 12

            num_videos = input("请输入要观看的视频数量 (默认12个): ").strip()
            num_videos = int(num_videos) if num_videos.isdigit() else 12

            read_articles(driver, num_articles)
            watch_videos(driver, num_videos)
            check_score(driver)
        elif choice == '0':
            print("正在退出程序...")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-logging "  # 禁用所有日志（激进）
    "--log-level=0 "      # 只显示 FATAL 错误（推荐）
    "--disable-features=EdgeQQBrowserImporter "  # 禁用 QQ 浏览器检测
    "--ignore-certificate-errors "  # 忽略 SSL 错误（不安全，仅调试）
    "--vmodule=*/ssl/*=0,*/qqbrowser/*=0,*/gpu/*=0"
)
    launch_xuexi_website()
