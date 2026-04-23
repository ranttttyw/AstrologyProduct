const api = require('../../utils/api')

Page({
  data: {
    chartData: null,
    chartList: [],
    mainSign: {},
    birthDate: '',
    birthTime: '',
    birthCity: '',
    editing: false,
    saving: false,
    formDate: '',
    formTime: '',
    formCity: '',
  },

  onShow() {
    this.loadProfile()
  },

  async loadProfile() {
    try {
      const res = await api.getUserProfile()
      if (res.has_chart) {
        const list = []
        const chart = res.chart_summary
        const order = ['sun', 'moon', 'ascendant', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
        for (const key of order) {
          if (chart[key]) {
            list.push({
              key,
              ...chart[key],
              degree_text: chart[key].degree_text || '',
            })
          }
        }

        // 主星座（太阳）用于顶部展示
        const mainSign = chart.sun || {}

        this.setData({
          chartData: res.chart_summary,
          chartList: list,
          mainSign: mainSign,
          birthDate: res.birth_date || '',
          birthTime: res.birth_time || '',
          birthCity: res.birth_city || '',
          editing: false,
        })
        getApp().globalData.hasChart = true
      } else {
        this.setData({ editing: true })
      }
    } catch (err) {
      console.error('加载档案失败', err)
    }
  },

  startEdit() {
    this.setData({
      editing: true,
      formDate: this.data.birthDate || '',
      formTime: this.data.birthTime || '',
      formCity: this.data.birthCity || '',
    })
  },

  cancelEdit() {
    this.setData({ editing: false })
  },

  onDateChange(e) {
    this.setData({ formDate: e.detail.value })
  },

  onTimeChange(e) {
    this.setData({ formTime: e.detail.value })
  },

  onCityInput(e) {
    this.setData({ formCity: e.detail.value })
  },

  async saveChart() {
    const { formDate, formTime, formCity } = this.data

    if (!formDate) {
      wx.showToast({ title: '请选择出生日期', icon: 'none' })
      return
    }
    if (!formCity) {
      wx.showToast({ title: '请输入出生城市', icon: 'none' })
      return
    }

    this.setData({ saving: true })

    try {
      await api.bindChart(formDate, formTime, formCity)
      wx.showToast({ title: '星盘已生成 ✨', icon: 'success' })
      this.loadProfile()
    } catch (err) {
      console.error('保存失败', err)
      wx.showToast({ title: '保存失败，请重试', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },
})
