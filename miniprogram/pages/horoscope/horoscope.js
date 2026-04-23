const api = require('../../utils/api')

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']

function numToStars(n) {
  const full = '★'
  const empty = '☆'
  const num = Math.max(1, Math.min(5, n || 3))
  return full.repeat(num) + empty.repeat(5 - num)
}

Page({
  data: {
    dateText: '',
    weekday: '',
    horoscope: null,
    scores: {},
    loading: false,
    hasChart: false,
  },

  onShow() {
    const app = getApp()
    this.setData({ hasChart: app.globalData.hasChart })

    // 设置日期
    const now = new Date()
    this.setData({
      dateText: `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`,
      weekday: `星期${WEEKDAYS[now.getDay()]}`,
    })

    if (app.globalData.hasChart) {
      // 优先用全局缓存
      if (app.globalData.todayHoroscope) {
        this.applyHoroscope(app.globalData.todayHoroscope)
      } else {
        this.loadHoroscope()
      }
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
    this.setData({ horoscope: h, scores, loading: false })
  },

  async loadHoroscope() {
    this.setData({ loading: true })
    try {
      const res = await api.getTodayHoroscope()
      if (res.horoscope) {
        getApp().globalData.todayHoroscope = res.horoscope
        this.applyHoroscope(res.horoscope)
      } else {
        this.setData({ loading: false })
      }
    } catch (err) {
      console.error('运势加载失败', err)
      this.setData({ loading: false })
    }
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  goToChat() {
    wx.switchTab({ url: '/pages/chat/chat' })
  },
})
