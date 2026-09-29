"""
Dr.Wu
"""
import asyncio
import pygame
import random
import math
import sys


# =========================================================
#                    基础设置
# =========================================================

WIDTH = 1000
HEIGHT = 650
FPS = 60

TITLE = "Jump Jump - Python"

# 游戏区域上下边界
PLAY_TOP = 90
PLAY_BOTTOM = 575

# 物理
GRAVITY = 1350.0

# 最大蓄力时间
MAX_CHARGE_TIME = 0.95

# 镜头平滑速度
CAMERA_SMOOTH = 7.5

# Perfect 持续时间
PERFECT_DURATION = 1.0

# 死亡动画持续时间
DEATH_DURATION = 0.85


# =========================================================
#                    颜色
# =========================================================

BG_COLOR = (18, 22, 32)

PLATFORM_COLOR = (90, 220, 150)
PLATFORM_TOP_COLOR = (150, 255, 200)

PLAYER_COLOR = (245, 245, 245)
PLAYER_HEAD_COLOR = (255, 215, 120)

TEXT_COLOR = (240, 240, 240)
MUTED_COLOR = (160, 170, 190)

PERFECT_COLOR = (255, 220, 80)

DANGER_COLOR = (255, 100, 100)


# =========================================================
#                 游戏状态
# =========================================================

READY = 0
CHARGING = 1
JUMPING = 2
DYING = 3
GAMEOVER = 4


# =========================================================
#                    平台类
# =========================================================

class Platform:

    def __init__(self, x, y, width):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)

        # 平台厚度
        self.height = 16

    @property
    def center(self):
        return self.x + self.width / 2.0

    def draw(self, screen, camera_x, camera_y):

        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)

        rect = pygame.Rect(
            screen_x,
            screen_y,
            int(self.width),
            self.height
        )

        # 平台主体
        pygame.draw.rect(
            screen,
            PLATFORM_COLOR,
            rect,
            border_radius=6
        )

        # 平台顶部
        pygame.draw.rect(
            screen,
            PLATFORM_TOP_COLOR,
            pygame.Rect(
                screen_x,
                screen_y,
                int(self.width),
                4
            ),
            border_radius=4
        )


# =========================================================
#                   浮动文字
# =========================================================

class FloatingText:

    def __init__(self):
        self.active = False

        self.x = 0.0
        self.y = 0.0

        self.life = 0.0
        self.duration = PERFECT_DURATION

        self.text = ""

        self.color = PERFECT_COLOR

    def start(self, x, y, text, color):
        self.active = True

        self.x = x
        self.y = y

        self.life = self.duration

        self.text = text
        self.color = color

    def update(self, dt):

        if not self.active:
            return

        self.life -= dt

        # 向上飘
        self.y -= 55.0 * dt

        if self.life <= 0:
            self.life = 0
            self.active = False

    def draw(self, screen, camera_x, camera_y, font):

        if not self.active:
            return

        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)

        # 根据剩余时间渐渐透明
        alpha = int(
            255 *
            max(
                0.0,
                min(
                    1.0,
                    self.life / self.duration
                )
            )
        )

        text_surface = font.render(
            self.text,
            True,
            self.color
        )

        text_surface = text_surface.convert_alpha()

        text_surface.set_alpha(alpha)

        rect = text_surface.get_rect(
            center=(
                screen_x,
                screen_y
            )
        )

        screen.blit(
            text_surface,
            rect
        )


# =========================================================
#                     玩家
# =========================================================

class Player:

    def __init__(self):

        # 玩家 X 是人物中心
        self.x = 0.0

        # 玩家 Y 是人物顶部
        self.y = 0.0

        self.width = 28
        self.height = 52

        # 速度
        self.vx = 0.0
        self.vy = 0.0

        # 动画时间
        self.anim_time = 0.0

    @property
    def feet(self):
        return self.y + self.height

    def update_animation(self, dt):
        self.anim_time += dt

    def launch(self, power):

        # --------------------------------------------------
        # 蓄力越久：
        # 水平速度越快
        # --------------------------------------------------

        self.vx = (
            240.0 +
            power * 400.0
        )

        # --------------------------------------------------
        # 蓄力越久：
        # 跳得越高
        # --------------------------------------------------

        self.vy = -(
            470.0 +
            power * 100.0
        )

    def draw(self,
             screen,
             camera_x,
             camera_y,
             state,
             death_timer):

        sx = self.x - camera_x
        sy = self.y - camera_y

        # 人物动画相位
        phase = self.anim_time * 8.0

        # 轻微上下呼吸
        bob = math.sin(phase) * 1.5

        # =================================================
        #                    死亡动画
        # =================================================

        if state == DYING:

            t = min(
                1.0,
                death_timer / DEATH_DURATION
            )

            # 死亡后越来越倾斜
            tilt = t * 1.1

            head_x = sx
            head_y = sy + 8

            # 身体
            body_x = sx
            body_y = sy + 22

            pygame.draw.circle(
                screen,
                PLAYER_HEAD_COLOR,
                (
                    int(head_x),
                    int(head_y)
                ),
                9
            )

            # 身体
            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(body_x),
                    int(body_y)
                ),
                (
                    int(
                        body_x +
                        math.sin(tilt) * 18
                    ),
                    int(
                        body_y +
                        24
                    )
                ),
                5
            )

            # 死亡时四肢逐渐散开
            arm_angle = tilt + 0.6

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(body_x),
                    int(body_y + 6)
                ),
                (
                    int(
                        body_x -
                        math.cos(arm_angle) * 17
                    ),
                    int(
                        body_y +
                        math.sin(arm_angle) * 17
                    )
                ),
                4
            )

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(body_x),
                    int(body_y + 6)
                ),
                (
                    int(
                        body_x +
                        math.cos(arm_angle) * 17
                    ),
                    int(
                        body_y +
                        math.sin(arm_angle) * 17
                    )
                ),
                4
            )

            return

        # =================================================
        #                    站立
        # =================================================

        if state == READY:

            head_x = sx
            head_y = sy + bob + 8

            body_top = sy + bob + 18
            body_bottom = sy + bob + 35

            # 头
            pygame.draw.circle(
                screen,
                PLAYER_HEAD_COLOR,
                (
                    int(head_x),
                    int(head_y)
                ),
                9
            )

            # 身体
            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top)
                ),
                (
                    int(sx),
                    int(body_bottom)
                ),
                5
            )

            # 手臂
            arm = math.sin(phase) * 5

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top + 5)
                ),
                (
                    int(sx - 15),
                    int(body_top + 12 + arm)
                ),
                4
            )

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top + 5)
                ),
                (
                    int(sx + 15),
                    int(body_top + 12 - arm)
                ),
                4
            )

            # 腿
            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_bottom)
                ),
                (
                    int(sx - 9),
                    int(body_bottom + 17)
                ),
                4
            )

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_bottom)
                ),
                (
                    int(sx + 9),
                    int(body_bottom + 17)
                ),
                4
            )

            return

        # =================================================
        #                    蓄力
        # =================================================

        if state == CHARGING:

            # 身体压低
            head_x = sx
            head_y = sy + 14

            body_top = sy + 24
            body_bottom = sy + 36

            pygame.draw.circle(
                screen,
                PLAYER_HEAD_COLOR,
                (
                    int(head_x),
                    int(head_y)
                ),
                9
            )

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top)
                ),
                (
                    int(sx),
                    int(body_bottom)
                ),
                5
            )

            # 手臂向下
            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top + 3)
                ),
                (
                    int(sx - 14),
                    int(body_top + 14)
                ),
                4
            )

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top + 3)
                ),
                (
                    int(sx + 14),
                    int(body_top + 14)
                ),
                4
            )

            # 腿弯曲
            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_bottom)
                ),
                (
                    int(sx - 12),
                    int(body_bottom + 11)
                ),
                4
            )

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_bottom)
                ),
                (
                    int(sx + 12),
                    int(body_bottom + 11)
                ),
                4
            )

            return

        # =================================================
        #                    跳跃
        # =================================================

        if state == JUMPING:

            # 头
            head_y = sy + 8

            pygame.draw.circle(
                screen,
                PLAYER_HEAD_COLOR,
                (
                    int(sx),
                    int(head_y)
                ),
                9
            )

            body_top = sy + 18
            body_bottom = sy + 35

            pygame.draw.line(
                screen,
                PLAYER_COLOR,
                (
                    int(sx),
                    int(body_top)
                ),
                (
                    int(sx),
                    int(body_bottom)
                ),
                5
            )

            # ---------------------------------------------
            # 上升
            # ---------------------------------------------

            if self.vy < -50:

                swing = math.sin(
                    phase
                ) * 4

                # 手向上
                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_top + 5)
                    ),
                    (
                        int(sx - 14),
                        int(body_top - 10 + swing)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_top + 5)
                    ),
                    (
                        int(sx + 14),
                        int(body_top - 10 - swing)
                    ),
                    4
                )

                # 腿收起来
                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_bottom)
                    ),
                    (
                        int(sx - 11),
                        int(body_bottom + 5)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_bottom)
                    ),
                    (
                        int(sx + 11),
                        int(body_bottom + 5)
                    ),
                    4
                )

            # ---------------------------------------------
            # 下降
            # ---------------------------------------------

            elif self.vy > 50:

                swing = math.sin(
                    phase
                ) * 3

                # 手向下
                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_top + 5)
                    ),
                    (
                        int(sx - 16),
                        int(body_top + 14 + swing)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_top + 5)
                    ),
                    (
                        int(sx + 16),
                        int(body_top + 14 - swing)
                    ),
                    4
                )

                # 腿张开
                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_bottom)
                    ),
                    (
                        int(sx - 12),
                        int(body_bottom + 18)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_bottom)
                    ),
                    (
                        int(sx + 12),
                        int(body_bottom + 18)
                    ),
                    4
                )

            # ---------------------------------------------
            # 最高点
            # ---------------------------------------------

            else:

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_top + 5)
                    ),
                    (
                        int(sx - 14),
                        int(body_top + 2)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_top + 5)
                    ),
                    (
                        int(sx + 14),
                        int(body_top + 2)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_bottom)
                    ),
                    (
                        int(sx - 9),
                        int(body_bottom + 17)
                    ),
                    4
                )

                pygame.draw.line(
                    screen,
                    PLAYER_COLOR,
                    (
                        int(sx),
                        int(body_bottom)
                    ),
                    (
                        int(sx + 9),
                        int(body_bottom + 17)
                    ),
                    4
                )


# =========================================================
#                      游戏类
# =========================================================

class Game:

    def __init__(self):

        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            TITLE
        )

        self.clock = pygame.time.Clock()

        self.running = True

        # 字体
        self.font_big = pygame.font.SysFont(
            "Microsoft YaHei",
            42
        )

        self.font = pygame.font.SysFont(
            "Microsoft YaHei",
            26
        )

        self.font_small = pygame.font.SysFont(
            "Microsoft YaHei",
            20
        )

        self.platforms = []

        self.player = Player()

        self.float_text = FloatingText()

        self.score = 0

        self.current_platform = 0

        self.state = READY

        self.charge_time = 0.0

        self.camera_x = 0.0
        self.camera_y = 0.0

        self.message = ""

        self.message_timer = 0.0

        self.death_timer = 0.0

        self.reset()


    # =====================================================
    #                    重置游戏
    # =====================================================

    def reset(self):

        self.score = 0

        self.state = READY

        self.charge_time = 0.0

        self.camera_x = 0.0
        self.camera_y = 0.0

        self.message = "Hold SPACE to charge"

        self.message_timer = 2.0

        self.death_timer = 0.0

        self.float_text.active = False

        self.platforms.clear()

        # 起始平台
        start = Platform(
            100,
            480,
            200
        )

        self.platforms.append(
            start
        )

        self.current_platform = 0

        # 玩家位置
        self.player.x = (
            start.center
        )

        self.player.y = (
            start.y -
            self.player.height
        )

        self.player.vx = 0.0
        self.player.vy = 0.0

        self.player.anim_time = 0.0

        # 生成初始平台
        for _ in range(14):
            self.generate_platform()


    # =====================================================
    #               根据分数生成平台
    # =====================================================

    def generate_platform(self):

        last = self.platforms[-1]

        difficulty = min(
            self.score // 5,
            20
        )

        # -------------------------------------------------
        # 平台越来越短
        # -------------------------------------------------

        max_width = max(
            80,
            165 - difficulty * 3
        )

        min_width = max(
            62,
            max_width - 45
        )

        width = random.randint(
            int(min_width),
            int(max_width)
        )

        # -------------------------------------------------
        # 平台之间越来越远
        # -------------------------------------------------

        gap_min = (
            70 +
            difficulty * 2
        )

        gap_max = (
            105 +
            difficulty * 3
        )

        gap_min = min(
            gap_min,
            145
        )

        gap_max = min(
            gap_max,
            190
        )

        gap = random.randint(
            gap_min,
            gap_max
        )

        # -------------------------------------------------
        # 高度轻微随机
        # -------------------------------------------------

        y = last.y + random.randint(
            -45,
            45
        )

        y = max(
            PLAY_TOP + 80,
            min(
                PLAY_BOTTOM - 30,
                y
            )
        )

        new_x = (
            last.x +
            last.width +
            gap
        )

        new_platform = Platform(
            new_x,
            y,
            width
        )

        self.platforms.append(
            new_platform
        )


    # =====================================================
    #                 保证前方有平台
    # =====================================================

    def ensure_platforms(self):

        # 镜头前面不够平台
        target_x = (
            self.camera_x +
            WIDTH * 2.2
        )

        while (
            len(self.platforms) < 20
            or self.platforms[-1].x <
            target_x
        ):
            self.generate_platform()

        # -------------------------------------------------
        # 回收左边已经不用的平台
        # -------------------------------------------------

        if (
            len(self.platforms) > 28
            and self.current_platform > 8
        ):

            remove_count = 5

            self.platforms = (
                self.platforms[
                    remove_count:
                ]
            )

            self.current_platform -= (
                remove_count
            )


    # =====================================================
    #                    显示消息
    # =====================================================

    def show_message(
        self,
        text,
        duration
    ):

        self.message = text

        self.message_timer = (
            duration
        )


    # =====================================================
    #                  开始死亡动画
    # =====================================================

    def start_death(self):

        if self.state == DYING:
            return

        self.state = DYING

        self.death_timer = 0.0

        # 死亡以后速度降低一点
        self.player.vx *= 0.30

        # 稍微弹一下
        self.player.vy = -180.0

        self.show_message(
            "YOU FELL!",
            DEATH_DURATION
        )


    # =====================================================
    #                    开始跳跃
    # =====================================================

    def launch(self):

        power = (
            self.charge_time /
            MAX_CHARGE_TIME
        )

        power = max(
            0.0,
            min(
                1.0,
                power
            )
        )

        self.player.launch(
            power
        )

        self.charge_time = 0.0

        self.state = JUMPING


    # =====================================================
    #                    碰撞检测
    # =====================================================

    def check_landing(
        self,
        old_feet,
        new_feet
    ):

        # 只有向下运动才能落台
        if self.player.vy <= 0:
            return None

        # 先检查前方附近的平台
        for index, platform in enumerate(
            self.platforms
        ):

            # 玩家脚跨过平台顶部
            crossed = (
                old_feet <= platform.y
                and
                new_feet >= platform.y
            )

            if not crossed:
                continue

            # 玩家中心在平台范围内
            inside = (
                self.player.x >= platform.x
                and
                self.player.x <=
                platform.x +
                platform.width
            )

            if inside:
                return index

        return None


    # =====================================================
    #                    成功落台
    # =====================================================

    def land(
        self,
        platform_index
    ):

        platform = (
            self.platforms[
                platform_index
            ]
        )

        # 修正玩家位置
        self.player.y = (
            platform.y -
            self.player.height
        )

        # 垂直速度清零
        self.player.vy = 0.0

        # =================================================
        #        新的平台才增加分数
        # =================================================

        if platform_index > self.current_platform:

            self.current_platform = (
                platform_index
            )

            # 普通 +1
            self.score += 1

            # -------------------------------------------------
            # Perfect 判断
            # -------------------------------------------------

            distance = abs(
                self.player.x -
                platform.center
            )

            tolerance = (
                platform.width * 0.20
            )

            if distance <= tolerance:

                # 额外 +2
                # 总计 +3

                self.score += 2

                self.float_text.start(
                    self.player.x,
                    self.player.y - 20,
                    "PERFECT +3",
                    PERFECT_COLOR
                )

                self.show_message(
                    "PERFECT!",
                    0.5
                )

            else:

                self.float_text.start(
                    self.player.x,
                    self.player.y - 10,
                    "+1",
                    PLATFORM_TOP_COLOR
                )

                self.show_message(
                    "+1",
                    0.35
                )

            # 继续生成地图
            self.ensure_platforms()

        # =================================================
        #       如果玩家还按着空格，继续蓄力
        # =================================================

        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:

            self.state = CHARGING

            self.charge_time = 0.0

        else:

            self.state = READY


    # =====================================================
    #                      更新
    # =====================================================

    def update(self, dt):

        self.player.update_animation(
            dt
        )

        self.float_text.update(
            dt
        )

        # -------------------------------------------------
        # 消息计时
        # -------------------------------------------------

        if self.message_timer > 0:

            self.message_timer -= dt

            if self.message_timer < 0:
                self.message_timer = 0


        # -------------------------------------------------
        # 蓄力
        # -------------------------------------------------

        if self.state == CHARGING:

            self.charge_time += dt

            if (
                self.charge_time
                >
                MAX_CHARGE_TIME
            ):

                self.charge_time = (
                    MAX_CHARGE_TIME
                )

        # -------------------------------------------------
        # 跳跃
        # -------------------------------------------------

        elif self.state == JUMPING:

            old_feet = (
                self.player.feet
            )

            # 水平
            self.player.x += (
                self.player.vx *
                dt
            )

            # 垂直
            self.player.y += (
                self.player.vy *
                dt
            )

            # 重力
            self.player.vy += (
                GRAVITY *
                dt
            )

            new_feet = (
                self.player.feet
            )

            # 检查落台
            platform_index = (
                self.check_landing(
                    old_feet,
                    new_feet
                )
            )

            if platform_index is not None:

                self.land(
                    platform_index
                )

            else:

                # -------------------------------------------------
                # 掉落判断
                # -------------------------------------------------

                current = (
                    self.platforms[
                        self.current_platform
                    ]
                )

                if (
                    self.player.y
                    >
                    current.y + 180
                    and
                    self.player.vy > 0
                ):

                    self.start_death()

        # -------------------------------------------------
        # 死亡
        # -------------------------------------------------

        elif self.state == DYING:

            self.death_timer += dt

            # 继续往下掉
            self.player.x += (
                self.player.vx *
                dt
            )

            self.player.y += (
                self.player.vy *
                dt
            )

            self.player.vy += (
                GRAVITY *
                dt
            )

            if (
                self.death_timer
                >=
                DEATH_DURATION
            ):

                self.state = GAMEOVER


        # -------------------------------------------------
        # 落地小压缩
        # -------------------------------------------------

        if self.state == READY:

            # 逐渐恢复
            pass


        # -------------------------------------------------
        # 更新摄像机
        # -------------------------------------------------

        self.update_camera(
            dt
        )

        # -------------------------------------------------
        # 保证地图
        # -------------------------------------------------

        if self.state not in (
            DYING,
            GAMEOVER
        ):

            self.ensure_platforms()


    # =====================================================
    #                   更新摄像机
    # =====================================================

    def update_camera(
        self,
        dt
    ):

        # 死亡时暂时停止镜头追踪
        if self.state in (
            DYING,
            GAMEOVER
        ):
            return

        # -------------------------------------------------
        # 水平目标
        # -------------------------------------------------

        target_x = (
            self.player.x -
            WIDTH * 0.32
        )

        if target_x < 0:
            target_x = 0

        # -------------------------------------------------
        # 垂直目标
        # -------------------------------------------------

        target_y = (
            self.player.y -
            HEIGHT * 0.52
        )

        if target_y < 0:
            target_y = 0

        # -------------------------------------------------
        # 平滑插值
        # -------------------------------------------------

        factor = (
            1.0 -
            math.exp(
                -CAMERA_SMOOTH *
                dt
            )
        )

        self.camera_x += (
            target_x -
            self.camera_x
        ) * factor

        self.camera_y += (
            target_y -
            self.camera_y
        ) * factor


    # =====================================================
    #                   绘制背景
    # =====================================================

    def draw_background(self):

        self.screen.fill(
            BG_COLOR
        )

        # -------------------------------------------------
        # 背景大圆
        # -------------------------------------------------

        moon_x = int(
            780 -
            self.camera_x * 0.08
        )

        moon_y = int(
            150 -
            self.camera_y * 0.03
        )

        pygame.draw.circle(
            self.screen,
            (50, 56, 75),
            (
                moon_x,
                moon_y
            ),
            65
        )

        # -------------------------------------------------
        # 背景山
        # -------------------------------------------------

        mountain_points = [
            (0, HEIGHT),
            (0, 470),

            (
                160 -
                int(self.camera_x * 0.10),
                360
            ),

            (
                350 -
                int(self.camera_x * 0.10),
                470
            ),

            (
                520 -
                int(self.camera_x * 0.10),
                330
            ),

            (
                760 -
                int(self.camera_x * 0.10),
                470
            ),

            (
                960 -
                int(self.camera_x * 0.10),
                350
            ),

            (WIDTH, 470),

            (WIDTH, HEIGHT)
        ]

        pygame.draw.polygon(
            self.screen,
            (25, 31, 45),
            mountain_points
        )


    # =====================================================
    #                     绘制 UI
    # =====================================================

    def draw_ui(self):

        # -------------------------------------------------
        # 分数
        # -------------------------------------------------

        score_surface = (
            self.font_big.render(
                f"{self.score}",
                True,
                TEXT_COLOR
            )
        )

        score_rect = (
            score_surface.get_rect(
                center=(WIDTH // 2, 42)
            )
        )

        self.screen.blit(
            score_surface,
            score_rect
        )


        # -------------------------------------------------
        # 蓄力条
        # -------------------------------------------------

        bar_x = 30
        bar_y = HEIGHT - 48

        bar_width = 260
        bar_height = 18

        pygame.draw.rect(
            self.screen,
            (50, 55, 68),
            (
                bar_x,
                bar_y,
                bar_width,
                bar_height
            ),
            border_radius=9
        )

        power = (
            self.charge_time /
            MAX_CHARGE_TIME
        )

        power = max(
            0.0,
            min(
                1.0,
                power
            )
        )

        filled = int(
            bar_width * power
        )

        if filled > 0:

            pygame.draw.rect(
                self.screen,
                PERFECT_COLOR,
                (
                    bar_x,
                    bar_y,
                    filled,
                    bar_height
                ),
                border_radius=9
            )


        # 蓄力文字

        power_text = (
            self.font_small.render(
                "POWER",
                True,
                MUTED_COLOR
            )
        )

        self.screen.blit(
            power_text,
            (
                bar_x,
                bar_y - 24
            )
        )


        # -------------------------------------------------
        # 操作提示
        # -------------------------------------------------

        if self.state == READY:

            text = (
                "Hold SPACE to charge"
            )

            surface = (
                self.font_small.render(
                    text,
                    True,
                    MUTED_COLOR
                )
            )

            self.screen.blit(
                surface,
                (
                    WIDTH - 250,
                    HEIGHT - 42
                )
            )

        elif self.state == CHARGING:

            percent = int(
                power * 100
            )

            text = (
                f"CHARGING  {percent}%"
            )

            surface = (
                self.font_small.render(
                    text,
                    True,
                    PERFECT_COLOR
                )
            )

            self.screen.blit(
                surface,
                (
                    WIDTH - 250,
                    HEIGHT - 42
                )
            )

        elif self.state == JUMPING:

            text = "JUMP!"

            surface = (
                self.font_small.render(
                    text,
                    True,
                    TEXT_COLOR
                )
            )

            self.screen.blit(
                surface,
                (
                    WIDTH - 120,
                    HEIGHT - 42
                )
            )


        # -------------------------------------------------
        # 中间消息
        # -------------------------------------------------

        if (
            self.message_timer > 0
            and
            self.state != GAMEOVER
        ):

            alpha = int(
                255 *
                min(
                    1.0,
                    self.message_timer * 3
                )
            )

            surface = (
                self.font.render(
                    self.message,
                    True,
                    TEXT_COLOR
                )
            )

            surface = surface.convert_alpha()

            surface.set_alpha(
                alpha
            )

            rect = surface.get_rect(
                center=(
                    WIDTH // 2,
                    100
                )
            )

            self.screen.blit(
                surface,
                rect
            )


        # -------------------------------------------------
        # 游戏结束
        # -------------------------------------------------

        if self.state == GAMEOVER:

            overlay = (
                pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )
            )

            overlay.fill(
                (0, 0, 0, 145)
            )

            self.screen.blit(
                overlay,
                (0, 0)
            )

            title = (
                self.font_big.render(
                    "GAME OVER",
                    True,
                    DANGER_COLOR
                )
            )

            rect = title.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 - 55
                )
            )

            self.screen.blit(
                title,
                rect
            )


            final_score = (
                self.font.render(
                    f"Score: {self.score}",
                    True,
                    TEXT_COLOR
                )
            )

            rect = final_score.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2
                )
            )

            self.screen.blit(
                final_score,
                rect
            )


            restart = (
                self.font_small.render(
                    "Press SPACE to restart",
                    True,
                    MUTED_COLOR
                )
            )

            rect = restart.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 55
                )
            )

            self.screen.blit(
                restart,
                rect
            )


    # =====================================================
    #                      绘制
    # =====================================================

    def draw(self):

        self.draw_background()

        # -------------------------------------------------
        # 平台
        # -------------------------------------------------

        for platform in self.platforms:

            # 屏幕左边很远的平台不用画
            if (
                platform.x +
                platform.width
                <
                self.camera_x - 100
            ):
                continue

            # 右边太远也不用画
            if (
                platform.x
                >
                self.camera_x +
                WIDTH +
                100
            ):
                continue

            platform.draw(
                self.screen,
                self.camera_x,
                self.camera_y
            )


        # -------------------------------------------------
        # 玩家
        # -------------------------------------------------

        self.player.draw(
            self.screen,
            self.camera_x,
            self.camera_y,
            self.state,
            self.death_timer
        )


        # -------------------------------------------------
        # PERFECT 浮动文字
        # -------------------------------------------------

        self.float_text.draw(
            self.screen,
            self.camera_x,
            self.camera_y,
            self.font
        )


        # -------------------------------------------------
        # UI
        # -------------------------------------------------

        self.draw_ui()

        pygame.display.flip()


    # =====================================================
    #                    事件处理
    # =====================================================

    def handle_events(self):

        for event in pygame.event.get():

            # 关闭窗口
            if event.type == pygame.QUIT:

                self.running = False


            # ESC
            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    self.running = False


                # -----------------------------------------
                # GAME OVER → SPACE 重开
                # -----------------------------------------

                elif (
                    event.key ==
                    pygame.K_SPACE
                    and
                    self.state ==
                    GAMEOVER
                ):

                    self.reset()


                # -----------------------------------------
                # READY → 开始蓄力
                # -----------------------------------------

                elif (
                    event.key ==
                    pygame.K_SPACE
                    and
                    self.state ==
                    READY
                ):

                    self.state = CHARGING

                    self.charge_time = 0.0


            # ---------------------------------------------
            # 松开 SPACE
            # ---------------------------------------------

            elif event.type == pygame.KEYUP:

                if (
                    event.key ==
                    pygame.K_SPACE
                    and
                    self.state ==
                    CHARGING
                ):

                    self.launch()


    # =====================================================
    #                      游戏运行
    # =====================================================

    async def run(self):

        while self.running:

            dt = (
                self.clock.tick(FPS)
                / 1000.0
            )

            # 防止卡顿时 dt 太大
            dt = min(
                dt,
                0.033
            )

            self.handle_events()

            self.update(
                dt
            )

            self.draw()

            # pygbag 必须把控制权交还给浏览器
            await asyncio.sleep(0)

        pygame.quit()


# =========================================================
#                        MAIN
# =========================================================

if __name__ == "__main__":

    game = Game()

    asyncio.run(game.run())