from nicegui import ui

# 响应式变量
name = ui.label('NiceGUI')

# 输入框组件，用户输入时实时更新 name 标签
ui.input('您的名字').on('keydown.enter', lambda e: name.set_text(e.sender.value))

# 运行应用
ui.run()