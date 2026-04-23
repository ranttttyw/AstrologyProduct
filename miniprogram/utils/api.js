/**
 * API请求封装
 * 开发时改成你的本地IP，部署后改成线上域名
 */
const BASE_URL = 'http://localhost:8000'

/**
 * 通用请求函数
 */
function request(path, data = {}, method = 'POST') {
  const app = getApp()
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': app.globalData.token ? `Bearer ${app.globalData.token}` : '',
      },
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // token过期，重新登录
          app.login().then(() => {
            request(path, data, method).then(resolve).catch(reject)
          })
        } else {
          reject(res.data)
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

/**
 * 小程序登录
 */
function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        request('/api/login', { code: loginRes.code })
          .then(resolve)
          .catch(reject)
      },
      fail: reject,
    })
  })
}

/**
 * 发送聊天消息
 */
function chat(message) {
  return request('/api/chat', { message })
}

/**
 * 绑定星盘
 */
function bindChart(birthDate, birthTime, birthCity) {
  return request('/api/user/bindChart', {
    birth_date: birthDate,
    birth_time: birthTime,
    birth_city: birthCity,
  })
}

/**
 * 获取用户档案
 */
function getUserProfile() {
  return request('/api/user/profile', {}, 'GET')
}

/**
 * 获取今日运势
 */
function getTodayHoroscope() {
  return request('/api/horoscope/today', {}, 'GET')
}

/**
 * 设置昵称
 */
function setNickname(nickname) {
  return request('/api/user/nickname', { nickname })
}

/**
 * 设置用户信息（性别、职业）
 */
function setUserInfo(data) {
  return request('/api/user/info', data)
}

module.exports = {
  login,
  chat,
  bindChart,
  getUserProfile,
  getTodayHoroscope,
  setNickname,
  setUserInfo,
}
