import logging
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
            
            # 获取图片元素的src属性
            src = element.get_attribute('src')
            
            # 提取base64编码部分
            if src and 'base64,' in src:
                # 分割字符串，获取base64编码部分
                base64_data = src.split('base64,')[1]
                
                # 解码base64数据
                img_data = base64.b64decode(base64_data)
                
                # 使用PIL处理图片
                img = Image.open(BytesIO(img_data))
                
                # 保存图片
                img.save(output_path)
                
                # 验证文件是否存在
                if os.path.exists(output_path):
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

        # 初始化WebDriver
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)

        # 打开学习强国登录页面
        print("正在打开学习强国登录页面...")
        driver.get("https://pc.xuexi.cn/points/login.html")

        print("页面已打开，请扫描二维码登录...")
        output_path = extract_login_qrcode(driver)
        img = Image.open(output_path)
        img.show()
        
        # 等待用户登录成功
        if wait_for_login(driver):
            # 登录成功后删除二维码图片
            os.remove(output_path)
            # 显示功能菜单并处理用户选择
            show_menu(driver)
        else:
            print("登录失败")
            driver.quit()
            return

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭浏览器
        if 'driver' in locals():
            driver.quit()
            print("浏览器已关闭")

def read_articles(driver, num_articles=6, start_index=0):
    """
    阅读文章获取积分
    
    参数：
        driver: WebDriver实例
        num_articles: 要阅读的文章数量
        start_index: 从文章列表的第几篇文章开始阅读
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
        print(f"找到{len(article_links)}篇文章，计划阅读{read_count}篇，从第{start_index+1}篇开始")

        for i in range(read_count):
            # 重新获取文章列表，避免StaleElementReferenceException
            article_links = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='text-link-item-title']"))
            )

            # 计算实际的文章索引，使用模运算确保不会超出范围
            actual_index = (i + start_index) % len(article_links)
            print(f"正在阅读第 {actual_index+1}/{len(article_links)} 篇文章")
            
            # 点击对应索引的文章
            article_links[actual_index].click()

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

def watch_videos(driver, num_videos=6, start_index=0):
    """
    观看视频获取积分
    
    参数：
        driver: WebDriver实例
        num_videos: 要观看的视频数量
        start_index: 从视频列表的第几个视频开始观看
    """
    try:
        #print("正在跳转到视频页面...")
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
        print(f"计划观看{watch_count}个视频，从第{start_index+1}个开始")

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
                
                # 计算实际的视频索引，使用模运算确保不会超出范围
                actual_index = (i + start_index) % len(video_links)
                print(f"正在观看第 {actual_index+1}/{len(video_links)} 个视频")
                
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
                
                # 使用JavaScript点击元素可能更可靠，注意使用actual_index
                try:
                    driver.execute_script("arguments[0].click();", video_links[actual_index])
                except Exception as e:
                    print(f"点击视频时出错，尝试替代方法: {e}")
                    try:
                        video_links[actual_index].click()
                    except:
                        print("替代点击方法也失败，跳过此视频")
                        continue

                # 切换到新窗口及后续代码保持不变
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
                                print("视频开始播放")
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

def check_score(driver, verbose=False):
    """
    查看当前学习积分，并返回文章和视频的积分状态
    verbose: 是否显示详细信息
    """
    try:
        # 跳转到积分页面
        print("正在检查积分状态...")
        driver.get("https://pc.xuexi.cn/points/my-points.html")
        time.sleep(3)

        # 等待积分数据加载
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "my-points-content"))
        )

        # 提取各项积分详情
        article_points = {'current': 0, 'target': 12}
        video_points = {'current': 0, 'target': 12}

        try:
            score_cards = driver.find_elements(By.CLASS_NAME, "my-points-card")

            if verbose:
                print(f"\n积分详情: 找到 {len(score_cards)} 个积分卡片")

            # 只有在详细模式下才打印所有卡片
            if verbose:
                print("\n所有积分卡片标题:")
                for i, card in enumerate(score_cards):
                    try:
                        title = card.find_element(By.CLASS_NAME, "my-points-card-title").text
                        progress = card.find_element(By.CLASS_NAME, "my-points-card-text").text
                        print(f"{i + 1}. {title}: {progress}")
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
                                print(f"解析文章积分失败: {progress}, 错误: {e}")
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
                                print(f"解析视频积分失败: {progress}, 错误: {e}")
                except Exception as e:
                    if verbose:
                        print(f"获取积分卡片详情失败: {e}")

            # 简洁的积分汇总
            print(f"积分进度: 文章 {article_points['current']}/{article_points['target']} | " +
                        f"视频 {video_points['current']}/{video_points['target']}")
        except Exception as e:
            if verbose:
                print(f"获取积分详情失败: {e}")

        return {
            'article': article_points,
            'video': video_points
        }
    except Exception as e:
        if verbose:
            print(f"查看积分时发生错误: {e}")
        return {
            'article': {'current': 0, 'target': 12},
            'video': {'current': 0, 'target': 12}
        }

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
            print("\n===== 开始全自动学习 =====")
        
            # 初始化检查积分状态
            score_status = check_score(driver, verbose=False)
        
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
                print(f"当前进度: 文章 {article_percent}% | 视频 {video_percent}%")
        
                # 如果两种任务都已完成，退出循环
                if article_remaining <= 0 and video_remaining <= 0:
                    print("✅ 所有学习任务已完成！")
                    break
        
                # 自动完成文章阅读任务，从已阅读的文章数量开始
                if article_remaining > 0:
                    batch_articles = min(6, article_remaining)
                    # 传递已获得的文章积分作为起始索引
                    read_articles(driver, batch_articles, article_current)
        
                # 简短地检查积分状态
                score_status = check_score(driver, verbose=False)
        
                # 如果已完成所有任务，提前退出
                if score_status['article']['current'] >= article_target and score_status['video']['current'] >= video_target:
                    print("✅ 所有学习任务已完成！")
                    break
        
                # 自动完成视频观看任务，从已观看的视频数量开始
                if video_remaining > 0:
                    batch_videos = min(6, video_remaining)
                    # 传递已获得的视频积分作为起始索引
                    watch_videos(driver, batch_videos, video_current)
        
                # 再次检查积分状态
                score_status = check_score(driver, verbose=False)
        elif choice == '0':
            print("正在退出程序...")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    launch_xuexi_website()
