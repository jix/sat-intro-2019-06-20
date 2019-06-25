# Sorry, this is horrible code, I didn't have much time left when I decided to
# have an interactive viewer

import json
import sys
import argparse
from itertools import chain

from colormath.color_objects import HSVColor, sRGBColor
from colormath.color_conversions import convert_color

import pygame
from pygame.locals import *

parser = argparse.ArgumentParser(description='view a solution')
parser.add_argument('--scale', type=int, default=70, help='UI scale')
parser.add_argument('solution', type=str, help='solution file name')

args = parser.parse_args()

with open(args.solution) as solution_file:
    solution = json.load(solution_file)

present = [set(chain(*step)) for step in solution]

scale = args.scale
border = int(scale * 0.05) + 1

sol_height = len(solution[0])
sol_width = len(solution[0][0])

pygame.init()
pygame.mixer.quit()

display = pygame.display.set_mode(
    (sol_width * scale, sol_height * scale + scale // 2))
frame_step = 0

background = (0, 0, 0)


def color(item_id, mu=1.0):
    color = convert_color(
        HSVColor(item_id * 137.50776405003785, 0.9 * mu, 0.9 * mu), sRGBColor)

    return (
        int(255 * color.clamped_rgb_r),
        int(255 * color.clamped_rgb_g),
        int(255 * color.clamped_rgb_b),
    )


run = None

frame_start = pygame.time.get_ticks()
frame_rev = False

while True:
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == QUIT or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_LEFT:
                if frame_step >= 1:
                    frame_step -= 1
                    frame_start = now
                    frame_rev = True
            elif event.key == K_RIGHT:
                if frame_step + 1 < len(solution) * 2:
                    frame_step += 1
                    frame_start = now
                    frame_rev = False
            elif event.key == K_PAGEUP:
                frame_step = 0
            elif event.key == K_PAGEDOWN:
                frame_step = len(solution) * 2 - 1
            if event.key == K_UP:
                frame_step = max(0, frame_step - 20)
            elif event.key == K_DOWN:
                frame_step = min(len(solution) * 2 - 1, frame_step + 20)

            elif event.key == K_SPACE:
                run = now
        elif event.type == KEYUP:
            if event.key == K_SPACE:
                run = None

    while run and now >= run:
        run += 200
        if frame_step + 1 < len(solution) * 2:
            frame_step += 1
            frame_start = now
            frame_rev = False

    step = frame_step // 2
    frame = frame_step % 2

    pygame.display.set_caption(
        f'step {step + 1}/{len(solution)} frame {frame}')

    current = solution[step]
    present_prev = present[step - 1] if step > 0 else set()
    present_next = present[step + 1] if step + 1 < len(solution) else set()

    for i, row in enumerate(current):
        for j, cell in enumerate(row):
            cell_color = background
            if cell is not None:
                cell_new = cell not in present_prev
                cell_leave = cell not in present_next
                mu = 1.0
                if frame_rev:
                    if frame == 1.0:
                        if cell_leave:
                            mu = 0.0
                if not frame_rev:
                    if frame == 0:
                        if cell_new:
                            mu = min(1.0, (now - frame_start) * 5e-3)
                    else:
                        if cell_leave:
                            mu = 1.0 - min(1.0, (now - frame_start) * 5e-3)

                cell_color = color(cell, mu)
            pygame.draw.rect(
                display, cell_color, (j * scale, i * scale, scale, scale))

    for i, row in enumerate(current):
        for j, cell in enumerate(row):
            border_left = j == 0 or row[j - 1] != cell
            border_right = j == sol_width - 1 or row[j + 1] != cell

            border_top = i == 0 or current[i - 1][j] != cell
            border_bottom = i == sol_height - 1 or current[i + 1][j] != cell

            if border_left:
                pygame.draw.rect(
                    display, background, (
                        j * scale, i * scale - border,
                        border, scale + 2 * border))

            if border_right:
                pygame.draw.rect(
                    display, background, (
                        (j + 1) * scale - border, i * scale - border,
                        border, scale + 2 * border))

            if border_top:
                pygame.draw.rect(
                    display, background, (
                        j * scale - border, i * scale,
                        scale + 2 * border, border))

            if border_bottom:
                pygame.draw.rect(
                    display, background, (
                        j * scale - border, (i + 1) * scale - border,
                        scale + 2 * border, border))

    pygame.draw.rect(
        display, background, (
            0, sol_height * scale,
            sol_width * scale, scale // 2))

    pygame.draw.rect(
        display, (200, 200, 200), (
            border * 2,
            sol_height * scale + 2 * border,
            (sol_width * scale - 4 * border) *
            frame_step / (2 * len(solution) - 1),
            scale // 2 - 4 * border))

    pygame.time.wait(10)
    pygame.display.update()
