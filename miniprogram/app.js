App({
  globalData: {
    token: '',
    hasChart: false,
    userProfile: null,
    nickname: '',
    todayHoroscope: null,  // 缓存今日运势
  },

  onLaunch() {
    this.login()
  },

  async login() {
    const api = require('./utils/api')
    try {
      const res = await api.login()
      this.globalData.token = res.token
      this.globalData.hasChart = res.has_chart
      console.log('登录成功', res.is_new_user ? '(新用户)' : '(老用户)')

      // 登录后加载用户信息
      if (res.has_chart) {
        this.loadProfile()
        this.loadTodayHoroscope()
      }
    } catch (err) {
      console.error('登录失败', err)
    }
  },

  async loadProfile() {
    const api = require('./utils/api')
    try {
      const res = await api.getUserProfile()
      this.globalData.nickname = res.nickname || ''
      this.globalData.userProfile = res
    } catch (err) {
      console.error('加载档案失败', err)
    }
  },

  async loadTodayHoroscope() {
    const api = require('./utils/api')
    try {
      const res = await api.getTodayHoroscope()
      if (res.horoscope) {
        this.globalData.todayHoroscope = res.horoscope
      }
    } catch (err) {
      console.error('加载运势失败', err)
    }
  },
})
