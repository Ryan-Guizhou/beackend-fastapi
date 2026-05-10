import request from '@/axios'
import type { ApiResponse } from '@/types/auth'

/**
 * Generic Page Request
 */
export interface PageRequest {
  page?: number
  pageSize?: number
  keyword?: string
}

/**
 * Generic Page Response
 */
export interface PageResponse<T> {
  items: T[]
  total: number
  hasNext?: boolean
}

// --- User Management ---

export interface UserInfo {
  id: string
  userCode: string
  userName: string
  mobilePhone?: string
  email?: string
  status: number
  createTime: string
  password?: string
}

export function pageUsers(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<UserInfo>>>('/core/user/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createUser(data: Partial<UserInfo>) {
  return request<ApiResponse<UserInfo>>('/core/user', {
    method: 'POST',
    data,
  })
}

export function updateUser(id: string, data: Partial<UserInfo>) {
  return request<ApiResponse<UserInfo>>(`/core/user/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteUser(id: string) {
  return request<ApiResponse<void>>(`/core/user/${id}`, {
    method: 'DELETE',
  })
}

// --- Menu Management ---

export interface MenuInfo {
  id: string
  menuName: string
  menuCode: string
  parentMenuId?: string
  menuUrl?: string
  sortNo?: number
  isShow: number
  status: number
}

export function pageMenus(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<MenuInfo>>>('/core/menu/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createMenu(data: Partial<MenuInfo>) {
  return request<ApiResponse<MenuInfo>>('/core/menu', {
    method: 'POST',
    data,
  })
}

export function updateMenu(id: string, data: Partial<MenuInfo>) {
  return request<ApiResponse<MenuInfo>>(`/core/menu/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteMenu(id: string) {
  return request<ApiResponse<void>>(`/core/menu/${id}`, {
    method: 'DELETE',
  })
}

// --- Router Management ---

export interface RouterInfo {
  id: string
  routerCode: string
  routerName: string
  routerUrl: string
  filePath: string
  moduleCode: string
}

export function pageRouters(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<RouterInfo>>>('/core/router/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createRouter(data: Partial<RouterInfo>) {
  return request<ApiResponse<RouterInfo>>('/core/router', {
    method: 'POST',
    data,
  })
}

export function updateRouter(id: string, data: Partial<RouterInfo>) {
  return request<ApiResponse<RouterInfo>>(`/core/router/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteRouter(id: string) {
  return request<ApiResponse<void>>(`/core/router/${id}`, {
    method: 'DELETE',
  })
}

// --- Resource Management ---

export interface ResourceInfo {
  id: string
  resourceCode: string
  resourceName: string
  resourceType: string
  resourceUrl?: string
  httpMethod?: string
  funcCode?: string
}

export function pageResources(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<ResourceInfo>>>('/core/resource/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createResource(data: Partial<ResourceInfo>) {
  return request<ApiResponse<ResourceInfo>>('/core/resource', {
    method: 'POST',
    data,
  })
}

export function updateResource(id: string, data: Partial<ResourceInfo>) {
  return request<ApiResponse<ResourceInfo>>(`/core/resource/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteResource(id: string) {
  return request<ApiResponse<void>>(`/core/resource/${id}`, {
    method: 'DELETE',
  })
}

// --- Function Management ---

export interface FunctionInfo {
  id: string
  funcCode: string
  funcName: string
  funcType?: string
  isMenu: number
  isDisable: number
  appCode?: string
}

export function pageFunctions(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<FunctionInfo>>>('/core/function/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createFunction(data: Partial<FunctionInfo>) {
  return request<ApiResponse<FunctionInfo>>('/core/function', {
    method: 'POST',
    data,
  })
}

export function updateFunction(id: string, data: Partial<FunctionInfo>) {
  return request<ApiResponse<FunctionInfo>>(`/core/function/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteFunction(id: string) {
  return request<ApiResponse<void>>(`/core/function/${id}`, {
    method: 'DELETE',
  })
}

// --- Dictionary Management ---

export interface DictInfo {
  id: string
  name: string
  code: string
  description?: string
  status: number
  createTime: string
}

export interface DictItemInfo {
  id: string
  dictCode: string
  label: string
  value: string
  sortNo: number
  description?: string
  status: number
  createTime: string
}

export function pageDicts(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<DictInfo>>>('/core/dict/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createDict(data: Partial<DictInfo>) {
  return request<ApiResponse<DictInfo>>('/core/dict', {
    method: 'POST',
    data,
  })
}

export function updateDict(id: string, data: Partial<DictInfo>) {
  return request<ApiResponse<DictInfo>>(`/core/dict/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteDict(id: string) {
  return request<ApiResponse<void>>(`/core/dict/${id}`, {
    method: 'DELETE',
  })
}

export function pageDictItems(params: PageRequest & { dictCode?: string }) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<DictItemInfo>>>('/core/dict_item/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function createDictItem(data: Partial<DictItemInfo>) {
  return request<ApiResponse<DictItemInfo>>('/core/dict_item', {
    method: 'POST',
    data,
  })
}

export function updateDictItem(id: string, data: Partial<DictItemInfo>) {
  return request<ApiResponse<DictItemInfo>>(`/core/dict_item/${id}`, {
    method: 'PUT',
    data,
  })
}

export function deleteDictItem(id: string) {
  return request<ApiResponse<void>>(`/core/dict_item/${id}`, {
    method: 'DELETE',
  })
}

// --- Audit Logs ---

export interface LoginLogInfo {
  id: string
  userCode: string
  userName: string
  clientIp: string
  browser?: string
  os?: string
  status: string
  msg?: string
  loginTime: string
}

export interface AuthLogInfo {
  id: string
  traceId: string
  actionType: string
  objectType: string
  operatorCode: string
  operatorName: string
  targetPartyCode: string
  targetPartyType: string
  targetPartyName: string
  authDesc?: string
  result: string
  clientIp: string
  operateTime: string
}

export function pageLoginLogs(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<LoginLogInfo>>>('/core/login_log/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}

export function pageAuthLogs(params: PageRequest) {
  const { page, ...rest } = params
  return request<ApiResponse<PageResponse<AuthLogInfo>>>('/core/auth_log/page_list', {
    method: 'GET',
    params: { pageIndex: page, ...rest },
  })
}
