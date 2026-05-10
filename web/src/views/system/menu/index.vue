<script setup lang="ts">
import { ref, onMounted, reactive, createVNode } from 'vue'
import {
  pageMenus,
  createMenu,
  updateMenu,
  deleteMenu,
  type MenuInfo,
} from '@/api/system-service'
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

const loading = ref(false)
const dataSource = ref<MenuInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '菜单名称', dataIndex: 'menuName', key: 'menuName' },
  { title: '菜单编码', dataIndex: 'menuCode', key: 'menuCode' },
  { title: '菜单URL', dataIndex: 'menuUrl', key: 'menuUrl' },
  { title: '排序', dataIndex: 'sortNo', key: 'sortNo' },
  { title: '显示', dataIndex: 'isShow', key: 'isShow' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', fixed: 'right', width: 150 },
]

// Modal State
const modalVisible = ref(false)
const modalTitle = ref('新增菜单')
const confirmLoading = ref(false)
const formRef = ref<FormInstance>()
const formState = reactive<Partial<MenuInfo>>({
  id: '',
  menuName: '',
  menuCode: '',
  parentMenuId: '',
  menuUrl: '',
  sortNo: 1,
  isShow: 1,
  status: 1,
})

const rules = {
  menuName: [{ required: true, message: '请输入菜单名称' }],
  menuCode: [{ required: true, message: '请输入菜单编码' }],
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageMenus(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取菜单列表失败')
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  queryParams.page = 1
  fetchData()
}

const onReset = () => {
  queryParams.keyword = ''
  queryParams.page = 1
  fetchData()
}

const onTableChange = (pagination: any) => {
  queryParams.page = pagination.current
  queryParams.pageSize = pagination.pageSize
  fetchData()
}

// CRUD Operations
const handleAdd = () => {
  modalTitle.value = '新增菜单'
  Object.assign(formState, {
    id: '',
    menuName: '',
    menuCode: '',
    parentMenuId: '',
    menuUrl: '',
    sortNo: 1,
    isShow: 1,
    status: 1,
  })
  modalVisible.value = true
}

const handleEdit = (record: MenuInfo) => {
  modalTitle.value = '编辑菜单'
  Object.assign(formState, { ...record })
  modalVisible.value = true
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该菜单吗？此操作不可撤销。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteMenu(id)
        message.success('删除成功')
        fetchData()
      } catch (error) {
        message.error('删除失败')
      }
    },
  })
}

const handleModalOk = async () => {
  try {
    await formRef.value?.validateFields()
    confirmLoading.value = true
    
    if (formState.id) {
      await updateMenu(formState.id, formState)
      message.success('更新成功')
    } else {
      await createMenu(formState)
      message.success('创建成功')
    }
    
    modalVisible.value = false
    fetchData()
  } catch (error) {
    console.error('Validation/API error:', error)
  } finally {
    confirmLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="menu-management">
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="关键字">
          <a-input v-model:value="queryParams.keyword" placeholder="名称/编码" allow-clear @press-enter="onSearch" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="onSearch">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
            <a-button @click="onReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card :bordered="false" class="table-card">
      <template #extra>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增菜单
        </a-button>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="{
          current: queryParams.page,
          pageSize: queryParams.pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条`
        }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'isShow'">
            <a-tag :color="record.isShow === 1 ? 'processing' : 'default'">
              {{ record.isShow === 1 ? '显示' : '隐藏' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 1 ? 'success' : 'error'">
              {{ record.status === 1 ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Add/Edit Modal -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :confirm-loading="confirmLoading"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item label="菜单名称" name="menuName">
          <a-input v-model:value="formState.menuName" placeholder="请输入菜单名称" />
        </a-form-item>
        <a-form-item label="菜单编码" name="menuCode">
          <a-input v-model:value="formState.menuCode" placeholder="请输入菜单编码" />
        </a-form-item>
        <a-form-item label="菜单URL" name="menuUrl">
          <a-input v-model:value="formState.menuUrl" placeholder="请输入菜单URL" />
        </a-form-item>
        <a-form-item label="父级菜单ID" name="parentMenuId">
          <a-input v-model:value="formState.parentMenuId" placeholder="请输入父级菜单ID (可选)" />
        </a-form-item>
        <a-form-item label="排序" name="sortNo">
          <a-input-number v-model:value="formState.sortNo" :min="1" style="width: 100%" />
        </a-form-item>
        <a-form-item label="是否显示" name="isShow">
          <a-radio-group v-model:value="formState.isShow">
            <a-radio :value="1">显示</a-radio>
            <a-radio :value="0">隐藏</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="formState.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.menu-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.search-card {
  border-radius: 8px;
}
.table-card {
  border-radius: 8px;
}
</style>
