const api = require('../../utils/api')

// 将评分数字转为星星
function numToStars(n) {
  const full = '★'
  const empty = '☆'
  const num = Math.max(1, Math.min(5, n || 3))
  return full.repeat(num) + empty.repeat(5 - num)
}

Page({
  data: {
    messages: [],
    inputText: '',
    isLoading: false,
    hasChart: false,
    scrollToId: '',
    horoscope: null,
    scores: {},
  },

  onShow() {
    const app = getApp()
    this.setData({ hasChart: app.globalData.hasChart })
    this.loadHoroscope()
  },

  async loadHoroscope() {
    const app = getApp()
    if (!app.globalData.hasChart) return

    // 先看全局缓存
    if (app.globalData.todayHoroscope) {
      this.applyHoroscope(app.globalData.todayHoroscope)
      return
    }

    // 没有缓存就请求
    try {
      const res = await api.getTodayHoroscope()
      if (res.horoscope) {
        app.globalData.todayHoroscope = res.horoscope
        this.applyHoroscope(res.horoscope)
      }
    } catch (err) {
      console.error('运势加载失败', err)
    }
  },

  applyHoroscope(h) {
    const rawScores = h.scores || {}
    const scores = {
      overall: numToStars(rawScores.overall),
      love: numToStars(rawScores.love),
      career: numToStars(rawScores.career),
      finance: numToStars(rawScores.finance),
      health: numToStars(rawScores.health),
    }
    this.setData({ horoscope: h, scores })
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  // 发送消息
  async sendMessage() {
    const text = this.data.inputText.trim()
    if (!text || this.data.isLoading) return

    // 添加用户消息
    const userMsg = { id: 'u' + Date.now(), role: 'user', content: text }
    this.setData({
      messages: [...this.data.messages, userMsg],
      inputText: '',
      isLoading: true,
      scrollToId: 'msg-loading',
    })

    try {
      const res = await api.chat(text)
      const botMsg = { id: 'b' + Date.now(), role: 'bot', content: res.reply }
      this.setData({
        messages: [...this.data.messages, botMsg],
        isLoading: false,
        scrollToId: 'msg-' + botMsg.id,
      })
    } catch (err) {
      console.error('聊天出错', err)
      const errorMsg = {
        id: 'e' + Date.now(),
        role: 'bot',
        content: '信号有点不稳定，稍后再试试～',
      }
      this.setData({
        messages: [...this.data.messages, errorMsg],
        isLoading: false,
      })
    }
  },

  // 快捷提问
  quickAsk(e) {
    const q = e.currentTarget.dataset.q
    this.setData({ inputText: q }, () => {
      this.sendMessage()
    })
  },

  // 跳转星盘设置
  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },
})
