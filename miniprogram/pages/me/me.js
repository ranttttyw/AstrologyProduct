const api = require('../../utils/api')

Page({
  data: {
    hasChart: false,
    sunSign: '',
    nickname: '',
    gender: '',
    occupation: '',
    editingNickname: false,
    nicknameInput: '',
    editingOccupation: false,
    occupationInput: '',
  },

  onShow() {
    this.loadProfile()
  },

  async loadProfile() {
    const app = getApp()
    this.setData({ hasChart: app.globalData.hasChart })

    try {
      const res = await api.getUserProfile()
      const nickname = res.nickname || ''
      const gender = res.gender || ''
      const occupation = res.occupation || ''
      this.setData({ nickname, gender, occupation })
      app.globalData.nickname = nickname
      app.globalData.gender = gender
      app.globalData.occupation = occupation

      if (res.has_chart && res.chart_summary && res.chart_summary.sun) {
        this.setData({ sunSign: res.chart_summary.sun.sign })
      }
    } catch (err) {
      console.error('获取档案失败', err)
    }
  },

  // ── 昵称 ──
  startEditNickname() {
    this.setData({
      editingNickname: true,
      nicknameInput: this.data.nickname,
    })
  },

  onNicknameInput(e) {
    this.setData({ nicknameInput: e.detail.value })
  },

  async saveNickname() {
    const nickname = this.data.nicknameInput.trim()
    if (!nickname) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' })
      return
    }
    try {
      await api.setNickname(nickname)
      this.setData({ nickname, editingNickname: false })
      getApp().globalData.nickname = nickname
      wx.showToast({ title: '已更新', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: '设置失败', icon: 'none' })
    }
  },

  // ── 性别 ──
  async setGender(e) {
    const gender = e.currentTarget.dataset.val
    if (gender === this.data.gender) return  // 重复点击不请求
    try {
      await api.setUserInfo({ gender })
      this.setData({ gender })
      getApp().globalData.gender = gender
      wx.showToast({ title: '已更新', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: '设置失败', icon: 'none' })
    }
  },

  // ── 职业 ──
  startEditOccupation() {
    this.setData({
      editingOccupation: true,
      occupationInput: this.data.occupation,
    })
  },

  onOccupationInput(e) {
    this.setData({ occupationInput: e.detail.value })
  },

  pickOccupation(e) {
    const val = e.currentTarget.dataset.val
    this.setData({ occupationInput: val })
    this.saveOccupation()
  },

  async saveOccupation() {
    const occupation = (this.data.occupationInput || '').trim()
    if (!occupation) {
      wx.showToast({ title: '请输入职业', icon: 'none' })
      return
    }
    try {
      await api.setUserInfo({ occupation })
      this.setData({ occupation, editingOccupation: false })
      getApp().globalData.occupation = occupation
      wx.showToast({ title: '已更新', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: '设置失败', icon: 'none' })
    }
  },

  // ── 导航 ──
  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },
  goToChat() {
    wx.switchTab({ url: '/pages/chat/chat' })
  },
})
