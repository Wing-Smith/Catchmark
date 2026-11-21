import pygame
import sys
import math
from pygame.locals import *

# 初始化pygame
pygame.init()

# 屏幕设置 - 加宽窗口
WIDTH, HEIGHT = 1000, 600  # 宽度从800增加到1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("F1赛道信号灯牌模拟 - 2025赛季")

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 120, 255)
LIGHT_BLUE = (173, 216, 230)

# 区域定义
FLAG_AREA_WIDTH = 800  # 旗帜显示区域保持800宽度
INFO_AREA_WIDTH = WIDTH - FLAG_AREA_WIDTH  # 信息区域200宽度
FLAG_AREA = pygame.Rect(0, 0, FLAG_AREA_WIDTH, HEIGHT)
INFO_AREA = pygame.Rect(FLAG_AREA_WIDTH, 0, INFO_AREA_WIDTH, HEIGHT)

# 2025赛季F1车手号码及车队信息 - 更新版（角田裕毅与劳森互换车队）
ALL_DRIVER_NUMBERS = {
    K_q: ("1", "维斯塔潘", "红牛"),
    K_w: ("4", "诺里斯", "迈凯伦"),
    K_e: ("5", "博托莱托", "索伯"),
    K_r: ("6", "哈贾尔", "小红牛"),
    K_t: ("43", "科拉平托", "Alpine"),
    K_y: ("10", "加斯利", "Alpine"),
    K_u: ("12", "安东内利", "梅奔"),
    K_i: ("14", "阿隆索", "阿斯顿马丁"),
    K_o: ("16", "勒克莱尔", "法拉利"),
    K_p: ("18", "斯托尔", "阿斯顿马丁"),
    K_a: ("22", "角田裕毅", "红牛"),  # 更新：从小红牛升至红牛车队
    K_s: ("23", "阿尔本", "威廉姆斯"),
    K_d: ("27", "霍肯博格", "索伯"),
    K_f: ("30", "劳森", "小红牛"),  # 更新：从红牛车队降至小红牛
    K_g: ("31", "奥康", "哈斯"),
    K_h: ("44", "汉密尔顿", "法拉利"),
    K_j: ("55", "赛恩斯", "威廉姆斯"),
    K_k: ("63", "拉塞尔", "梅奔"),
    K_l: ("81", "皮亚斯特里", "迈凯伦"),
    K_z: ("87", "贝尔曼", "哈斯")
}

# 信号类型 - 修改闪烁频率
SIGNALS = {
    K_1: {"name": "绿旗", "color": GREEN, "flash": True, "pattern": None, "animation": None, "text": None, "flash_rate": 2.5},  # 每秒2.5次
    K_2: {"name": "黄旗", "color": YELLOW, "flash": True, "pattern": None, "animation": None, "text": None, "flash_rate": 3.0},  # 每秒3次
    K_3: {"name": "红旗", "color": RED, "flash": True, "pattern": None, "animation": None, "text": None, "flash_rate": 2.0},  # 每秒2次
    K_4: {"name": "蓝旗", "color": BLUE, "flash": True, "pattern": None, "animation": None, "text": None, "type": "blue_flag", "flash_rate": 3.0},  # 每秒3次
    K_5: {"name": "黑白对角旗", "color": None, "flash": True, "pattern": "checker_diagonal", "animation": None, "text": None, "flash_rate": 3.0},  # 每秒3次
    K_6: {"name": "方格旗", "color": None, "flash": True, "pattern": "checker", "animation": None, "text": None, "flash_rate": 3.0},  # 每秒3次
    K_7: {"name": "雨地", "color": BLACK, "flash": False, "pattern": None, "animation": "rain", "text": None, "flash_rate": 0},  # 不闪烁，黑色背景
    K_8: {"name": "安全车", "color": None, "flash": True, "pattern": None, "animation": None, "text": "SC", "border": True, "flash_rate": 3.0},  # 每秒3次
    K_9: {"name": "虚拟安全车", "color": None, "flash": True, "pattern": None, "animation": None, "text": "VSC", "border": True, "flash_rate": 3.0},  # 每秒3次
    K_0: {"name": "黑橙圆点旗", "color": None, "flash": True, "pattern": "black_orange", "animation": None, "text": None, "flash_rate": 3.0}  # 每秒3次
}

# 程序状态
class ProgramState:
    def __init__(self):
        self.current_signal = SIGNALS[K_1]
        self.flash_state = True
        self.flash_timer = 0
        self.standby_mode = False  # 待机状态
        self.blue_flag_mode = False  # 蓝旗特殊模式
        self.driver_number = ""  # 车手号码
        self.driver_name = ""   # 车手姓名
        self.driver_team = ""   # 车手车队
        self.blue_flag_phase = 0  # 蓝旗显示阶段: 0-选择号码, 1-显示号码, 2-显示蓝旗
        self.animation_counter = 0  # 动画计数器
        self.blue_flag_flash_timer = 0  # 蓝旗特殊闪烁计时器
        self.rain_offset = 0.0  # 改为浮点数以提高精度

program_state = ProgramState()

# 字体
font_medium = pygame.font.SysFont('simhei', 36)
font_small = pygame.font.SysFont('simhei', 20)
font_tiny = pygame.font.SysFont('simhei', 16)
font_huge = pygame.font.SysFont('simhei', 160)  # 加大字号用于蓝旗车号（占65%以上）
font_sc_vsc = pygame.font.SysFont('simhei', 140)  # 加大SC/VSC字号（占65%以上）

def get_flash_interval(flash_rate):
    """根据闪烁频率计算帧间隔"""
    if flash_rate == 0:
        return 0
    # 60帧/秒 ÷ 闪烁频率 = 完整周期帧数，再÷2得到亮/灭各占帧数
    return int(60 / flash_rate / 2)

def draw_driver_number_large(number):
    """绘制大字号车手号码（仅显示号码，占窗口65%以上）"""
    # 只在旗帜区域绘制
    screen.fill(BLACK, FLAG_AREA)
    
    # 超大字号车手号码（占旗帜区域65%以上）
    number_text = font_huge.render(number, True, WHITE)
    text_width = number_text.get_width()
    text_height = number_text.get_height()
    
    # 计算位置使其占据旗帜区域的65%以上
    target_width = FLAG_AREA_WIDTH * 0.65
    scale_factor = target_width / text_width if text_width > 0 else 1
    scaled_font_size = int(160 * scale_factor)
    
    # 创建临时字体来适应大小
    temp_font = pygame.font.SysFont('simhei', min(scaled_font_size, 200))
    scaled_text = temp_font.render(number, True, WHITE)
    
    screen.blit(scaled_text, (
        FLAG_AREA_WIDTH // 2 - scaled_text.get_width() // 2,
        HEIGHT // 2 - scaled_text.get_height() // 2
    ))

def draw_blue_flag():
    """绘制蓝旗（只显示蓝色背景，不显示文字）"""
    screen.fill(BLUE, FLAG_AREA)

def draw_rain_animation():
    """绘制雨地动画（黑色背景 + 巨大💦emoji连续滚动）"""
    # 黑色背景
    screen.fill(BLACK, FLAG_AREA)
    
    # 加快2.5倍速度滚动
    program_state.rain_offset += 5  # 从2像素/帧增加到5像素/帧
    
    # 创建巨大的💦emoji字体 - 填满整个旗帜区域
    emoji_size = min(FLAG_AREA_WIDTH, HEIGHT)  # 取宽高中的较小值作为emoji大小
    emoji_font = pygame.font.SysFont('segoeuiemoji', emoji_size)
    
    # 渲染💦emoji
    emoji_text = emoji_font.render("💦", True, WHITE)
    emoji_width = emoji_text.get_width()
    emoji_height = emoji_text.get_height()
    
    # 计算emoji位置使其填满屏幕
    x_pos = (FLAG_AREA_WIDTH - emoji_width) // 2
    
    # 绘制多个emoji实现连续滚动效果
    # 计算需要绘制的emoji数量，确保完全覆盖屏幕并连续滚动
    num_emojis = 3  # 绘制3个emoji确保连续滚动
    
    for i in range(num_emojis):
        y_pos = program_state.rain_offset + (i - 1) * emoji_height
        
        # 当第一个emoji完全滚出屏幕时，重置偏移量实现循环
        if program_state.rain_offset > emoji_height:
            program_state.rain_offset = 0
        
        screen.blit(emoji_text, (x_pos, int(y_pos)))

def draw_info_panel():
    """绘制信息面板"""
    # 信息区域背景
    screen.fill((40, 40, 40), INFO_AREA)
    
    # 绘制分隔线
    pygame.draw.line(screen, WHITE, (FLAG_AREA_WIDTH, 0), (FLAG_AREA_WIDTH, HEIGHT), 2)
    
    y_pos = 20
    
    # 当前状态标题
    status_title = font_small.render("当前状态", True, YELLOW)
    screen.blit(status_title, (FLAG_AREA_WIDTH + 10, y_pos))
    y_pos += 30
    
    # 显示当前信号
    if program_state.standby_mode:
        status_text = font_tiny.render("待机状态", True, GREEN)
    elif program_state.blue_flag_mode:
        if program_state.blue_flag_phase == 0:
            status_text = font_tiny.render("选择车手", True, BLUE)
        elif program_state.blue_flag_phase == 1:
            status_text = font_tiny.render("车号闪烁", True, BLUE)
        else:
            status_text = font_tiny.render("蓝旗闪烁", True, BLUE)
    else:
        status_text = font_tiny.render(program_state.current_signal["name"], True, WHITE)
    
    screen.blit(status_text, (FLAG_AREA_WIDTH + 10, y_pos))
    y_pos += 40
    
    # 蓝旗相关信息
    if program_state.blue_flag_mode and program_state.driver_number:
        driver_title = font_small.render("蓝旗车手", True, BLUE)
        screen.blit(driver_title, (FLAG_AREA_WIDTH + 10, y_pos))
        y_pos += 25
        
        driver_info = font_tiny.render(f"{program_state.driver_number} {program_state.driver_name}", True, WHITE)
        screen.blit(driver_info, (FLAG_AREA_WIDTH + 10, y_pos))
        y_pos += 20
        
        team_info = font_tiny.render(program_state.driver_team, True, YELLOW)
        screen.blit(team_info, (FLAG_AREA_WIDTH + 10, y_pos))
        y_pos += 40
    
    # 操作说明
    instructions_title = font_small.render("操作说明", True, YELLOW)
    screen.blit(instructions_title, (FLAG_AREA_WIDTH + 10, y_pos))
    y_pos += 25
    
    instructions = [
        "1-9,0: 切换信号",
        "4: 蓝旗模式",
        "空格: 待机",
        "ESC: 取消选择",
        "回车: 确认"
    ]
    
    for instruction in instructions:
        text = font_tiny.render(instruction, True, WHITE)
        screen.blit(text, (FLAG_AREA_WIDTH + 10, y_pos))
        y_pos += 20
    
    y_pos += 20
    
    # 信号列表
    signals_title = font_small.render("信号列表", True, YELLOW)
    screen.blit(signals_title, (FLAG_AREA_WIDTH + 10, y_pos))
    y_pos += 25
    
    signals_list = [
        "1: 绿旗", "2: 黄旗", "3: 红旗",
        "4: 蓝旗", "5: 对角旗", "6: 方格旗",
        "7: 雨地", "8: 安全车", "9: VSC",
        "0: 黑橙旗"
    ]
    
    for signal_item in signals_list:
        text = font_tiny.render(signal_item, True, WHITE)
        screen.blit(text, (FLAG_AREA_WIDTH + 10, y_pos))
        y_pos += 18

def draw_keyboard_layout():
    """绘制键盘布局"""
    screen.fill(BLACK, FLAG_AREA)
    
    title_text = font_medium.render("2025赛季 - 选择被套圈车手 (20位车手)", True, YELLOW)
    screen.blit(title_text, (FLAG_AREA_WIDTH // 2 - title_text.get_width() // 2, 20))
    
    # 第一行: q w e r t y u i o p (10个键)
    keys_row1 = [K_q, K_w, K_e, K_r, K_t, K_y, K_u, K_i, K_o, K_p]
    for i, key in enumerate(keys_row1):
        x_pos = 80 + i * 65
        y_pos = 80
        
        # 绘制按键框
        key_rect = pygame.Rect(x_pos - 28, y_pos - 18, 56, 36)
        pygame.draw.rect(screen, BLUE, key_rect, 2)
        
        # 绘制按键标签
        key_label = font_tiny.render(pygame.key.name(key).upper(), True, WHITE)
        screen.blit(key_label, (x_pos - key_label.get_width() // 2, y_pos - 15))
        
        # 绘制车手号码
        number, name, team = ALL_DRIVER_NUMBERS[key]
        number_text = font_small.render(number, True, WHITE)
        screen.blit(number_text, (x_pos - number_text.get_width() // 2, y_pos))
    
    # 第二行: a s d f g h j k l (9个键)
    keys_row2 = [K_a, K_s, K_d, K_f, K_g, K_h, K_j, K_k, K_l]
    for i, key in enumerate(keys_row2):
        x_pos = 95 + i * 65
        y_pos = 130
        
        key_rect = pygame.Rect(x_pos - 28, y_pos - 18, 56, 36)
        pygame.draw.rect(screen, BLUE, key_rect, 2)
        
        key_label = font_tiny.render(pygame.key.name(key).upper(), True, WHITE)
        screen.blit(key_label, (x_pos - key_label.get_width() // 2, y_pos - 15))
        
        number, name, team = ALL_DRIVER_NUMBERS[key]
        number_text = font_small.render(number, True, WHITE)
        screen.blit(number_text, (x_pos - number_text.get_width() // 2, y_pos))
    
    # 第三行: z (1个键)
    keys_row3 = [K_z]
    for i, key in enumerate(keys_row3):
        x_pos = 95
        y_pos = 180
        
        key_rect = pygame.Rect(x_pos - 28, y_pos - 18, 56, 36)
        pygame.draw.rect(screen, BLUE, key_rect, 2)
        
        key_label = font_tiny.render(pygame.key.name(key).upper(), True, WHITE)
        screen.blit(key_label, (x_pos - key_label.get_width() // 2, y_pos - 15))
        
        number, name, team = ALL_DRIVER_NUMBERS[key]
        number_text = font_small.render(number, True, WHITE)
        screen.blit(number_text, (x_pos - number_text.get_width() // 2, y_pos))
    
    # 显示车手详细信息 - 分两列显示
    y_info = 230
    driver_list = list(ALL_DRIVER_NUMBERS.items())
    
    for i, (key, (number, name, team)) in enumerate(driver_list):
        if i < 10:  # 第一列
            x_info = 50
            y_pos = y_info + i * 25
        else:  # 第二列
            x_info = 400
            y_pos = y_info + (i-10) * 25
            
        key_name = pygame.key.name(key).upper()
        info_text = font_tiny.render(f"{key_name}: {number} {name} - {team}", True, WHITE)
        screen.blit(info_text, (x_info, y_pos))
    
    # 显示操作提示
    esc_text = font_small.render("按 ESC 取消选择", True, YELLOW)
    screen.blit(esc_text, (FLAG_AREA_WIDTH // 2 - esc_text.get_width() // 2, 480))
    
    # 显示当前选择的号码
    if program_state.driver_number:
        selected_text = font_medium.render(f"已选择: {program_state.driver_number} - {program_state.driver_name}", True, GREEN)
        screen.blit(selected_text, (FLAG_AREA_WIDTH // 2 - selected_text.get_width() // 2, 510))
        
        confirm_text = font_small.render("按回车键确认并继续", True, YELLOW)
        screen.blit(confirm_text, (FLAG_AREA_WIDTH // 2 - confirm_text.get_width() // 2, 540))

def draw_sc_vsc_display(text):
    """绘制SC和VSC显示（黑底白字，黄色边框）"""
    # 黑色背景（只在旗帜区域）
    screen.fill(BLACK, FLAG_AREA)
    
    # 绘制黄色边框（圆角矩形）
    border_rect = pygame.Rect(50, 50, FLAG_AREA_WIDTH - 100, HEIGHT - 100)
    if program_state.flash_state:  # 只有边框闪烁
        pygame.draw.rect(screen, YELLOW, border_rect, 5, border_radius=20)
    
    # 绘制文字（白色）- 使用加大字号，占旗帜区域65%以上
    text_surface = font_sc_vsc.render(text, True, WHITE)
    text_width = text_surface.get_width()
    text_height = text_surface.get_height()
    
    # 计算位置使其占据旗帜区域的65%以上
    target_width = FLAG_AREA_WIDTH * 0.65
    scale_factor = target_width / text_width if text_width > 0 else 1
    scaled_font_size = int(140 * scale_factor)
    
    # 创建临时字体来适应大小
    temp_font = pygame.font.SysFont('simhei', min(scaled_font_size, 180))
    scaled_text = temp_font.render(text, True, WHITE)
    
    screen.blit(scaled_text, (
        FLAG_AREA_WIDTH // 2 - scaled_text.get_width() // 2,
        HEIGHT // 2 - scaled_text.get_height() // 2
    ))

def handle_blue_flag_animation():
    """处理蓝旗特殊动画序列"""
    # 蓝旗特殊序列使用独立的较慢闪烁频率
    program_state.blue_flag_flash_timer += 1
    
    if program_state.blue_flag_phase == 0:
        # 阶段0: 选择车手号码
        draw_keyboard_layout()
        
    elif program_state.blue_flag_phase == 1:
        # 阶段1: 仅显示车号闪烁，闪烁时间减半
        if program_state.animation_counter < 6:  # 闪烁3次
            # 使用更快的闪烁频率（时间减半）
            show_number = (program_state.blue_flag_flash_timer < 10)  # 亮10帧，灭10帧（原来20帧）
            if show_number:
                draw_driver_number_large(program_state.driver_number)  # 使用大字号仅显示号码
            else:
                screen.fill(BLACK, FLAG_AREA)
            
            # 检查是否完成一次完整闪烁循环
            if program_state.blue_flag_flash_timer >= 20:  # 20帧完成一次亮灭循环
                program_state.blue_flag_flash_timer = 0
                program_state.animation_counter += 1
        else:
            program_state.blue_flag_phase = 2
            program_state.animation_counter = 0
            program_state.blue_flag_flash_timer = 0
    
    elif program_state.blue_flag_phase == 2:
        # 阶段2: 蓝旗闪烁三次（使用较慢频率）
        if program_state.animation_counter < 6:  # 闪烁3次
            # 使用蓝旗特殊闪烁计时器
            show_flag = (program_state.blue_flag_flash_timer < 20)  # 亮20帧，灭20帧
            if show_flag:
                draw_blue_flag()  # 只显示蓝色背景，不显示文字
            else:
                screen.fill(BLACK, FLAG_AREA)
            
            # 检查是否完成一次完整闪烁循环
            if program_state.blue_flag_flash_timer >= 40:  # 40帧完成一次亮灭循环
                program_state.blue_flag_flash_timer = 0
                program_state.animation_counter += 1
        else:
            # 动画完成，进入待机状态
            program_state.blue_flag_mode = False
            program_state.standby_mode = True
            program_state.blue_flag_phase = 0
            program_state.animation_counter = 0
            program_state.blue_flag_flash_timer = 0
            program_state.driver_number = ""
            program_state.driver_name = ""
            program_state.driver_team = ""

# 主循环
clock = pygame.time.Clock()
running = True

while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                # 空格键切换待机状态
                program_state.standby_mode = not program_state.standby_mode
                program_state.blue_flag_mode = False
                program_state.blue_flag_phase = 0
                program_state.driver_number = ""
                program_state.driver_name = ""
                program_state.driver_team = ""
            
            elif event.key == K_ESCAPE:
                if program_state.blue_flag_mode:
                    # ESC键取消蓝旗模式
                    program_state.blue_flag_mode = False
                    program_state.blue_flag_phase = 0
                    program_state.driver_number = ""
                    program_state.driver_name = ""
                    program_state.driver_team = ""
            
            elif program_state.blue_flag_mode and program_state.blue_flag_phase == 0:
                # 蓝旗模式下的号码选择
                if event.key in ALL_DRIVER_NUMBERS:
                    number, name, team = ALL_DRIVER_NUMBERS[event.key]
                    program_state.driver_number = number
                    program_state.driver_name = name
                    program_state.driver_team = team
                elif event.key == K_RETURN and program_state.driver_number:
                    # 回车键确认号码
                    program_state.blue_flag_phase = 1
                    program_state.animation_counter = 0
                    program_state.blue_flag_flash_timer = 0
            
            elif not program_state.standby_mode and not program_state.blue_flag_mode:
                # 正常信号切换
                if event.key in SIGNALS:
                    if event.key == K_4:  # 蓝旗特殊处理
                        program_state.blue_flag_mode = True
                        program_state.blue_flag_phase = 0
                        program_state.driver_number = ""
                        program_state.driver_name = ""
                        program_state.driver_team = ""
                    else:
                        program_state.current_signal = SIGNALS[event.key]
                        program_state.flash_state = True
                        program_state.flash_timer = 0
    
    # 更新主闪烁状态 - 根据当前信号的闪烁频率
    current_signal = program_state.current_signal
    flash_rate = current_signal.get("flash_rate", 3.0)  # 默认3次/秒
    
    if flash_rate > 0:  # 只有需要闪烁的信号才更新
        program_state.flash_timer += 1
        flash_interval = get_flash_interval(flash_rate)
        
        if flash_interval > 0 and program_state.flash_timer >= flash_interval:
            program_state.flash_state = not program_state.flash_state
            program_state.flash_timer = 0
    
    # 清屏
    screen.fill(BLACK)
    
    # 检查是否在待机状态
    if program_state.standby_mode:
        # 待机状态只显示黑色背景，不显示文字
        screen.fill(BLACK, FLAG_AREA)
    
    # 检查是否在蓝旗特殊模式
    elif program_state.blue_flag_mode:
        handle_blue_flag_animation()
    
    # 正常显示信号
    elif not program_state.blue_flag_mode:
        # 根据信号类型绘制不同内容（只在旗帜区域，不显示信号名称文字）
        signal = program_state.current_signal
        
        # 检查是否有特殊图案
        if signal["pattern"] == "checker_diagonal":
            # 绘制黑白对角旗 - 修复：对角线分割，两部分交替填充白色
            if program_state.flash_state:
                # 左上到右下对角线，左上部分白色
                screen.fill(BLACK, FLAG_AREA)
                pygame.draw.polygon(screen, WHITE, [
                    (0, 0), (FLAG_AREA_WIDTH, 0), (0, HEIGHT)
                ])
            else:
                # 左上到右下对角线，右下部分白色
                screen.fill(BLACK, FLAG_AREA)
                pygame.draw.polygon(screen, WHITE, [
                    (FLAG_AREA_WIDTH, 0), (FLAG_AREA_WIDTH, HEIGHT), (0, HEIGHT)
                ])
        
        elif signal["pattern"] == "checker":
            # 绘制方格旗
            cell_size = 40
            for y in range(0, HEIGHT, cell_size):
                for x in range(0, FLAG_AREA_WIDTH, cell_size):
                    if ((x // cell_size) + (y // cell_size)) % 2 == 0:
                        if program_state.flash_state:
                            color = WHITE
                        else:
                            color = BLACK
                    else:
                        if program_state.flash_state:
                            color = BLACK
                        else:
                            color = WHITE
                    pygame.draw.rect(screen, color, (x, y, cell_size, cell_size))
        
        elif signal["pattern"] == "black_orange":
            # 绘制黑橙圆点旗
            if program_state.flash_state:
                screen.fill(BLACK, FLAG_AREA)
                center_x, center_y = FLAG_AREA_WIDTH // 2, HEIGHT // 2
                radius = min(FLAG_AREA_WIDTH, HEIGHT) // 3
                
                # 绘制橙色圆点
                pygame.draw.circle(screen, (255, 165, 0), (center_x, center_y), radius)
            else:
                screen.fill(BLACK, FLAG_AREA)
        
        # 检查SC/VSC特殊显示
        elif signal.get("border"):
            draw_sc_vsc_display(signal["text"])
        
        # 检查是否有动画
        elif signal["animation"] == "rain":
            draw_rain_animation()
        
        # 普通彩色旗帜
        else:
            if not signal["flash"] or (signal["flash"] and program_state.flash_state):
                screen.fill(signal["color"], FLAG_AREA)
    
    # 绘制信息面板
    draw_info_panel()
    
    # 更新屏幕
    pygame.display.flip()
    clock.tick(60)

# 退出pygame
pygame.quit()
sys.exit()
