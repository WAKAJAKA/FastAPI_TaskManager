from fastapi import FastAPI, HTTPException, Path, status
from pydantic import BaseModel, Field

# Инициализация приложения с метаданными для Swagger UI
app = FastAPI(
    title="Task Manager API",
    description="Сервис для TaskManager.",
    version="1.0.0",
)

# Временное хранилище задач в оперативной памяти (ключ — числовой ID)
tasks_store: dict[int, dict] = {}
current_id: int = 0


class TaskCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Обязательно заголовок задачи (от 3 до 100 символов)",
        examples=["Назначить задачу для сбора метрики"],
    )
    description: str | None = Field(
        default=None,
        description="Необязательное подробное описание задачи",
        examples=["Собрать данные из CRM "],
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="Приоритет задачи: от 1 (Низкий) до 5 (Высокий)",
        examples=[4],
    )


class TaskResponse(TaskCreate):
    id: int = Field(
        ...,
        description="Уникальный числовой идентификатор задачи",
        examples=[1],
    )


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую задачу, с автоматическим назначением ID",
    description="Принимает данные задачи, генерирует порядковый ID в числовом формате,  данные находятся  в оперативной памяти. При каждом вызове ID увеличивается на единицу",
    response_description=" 201 Created (Данные  успешно созданной задачи с присвоенным ID)",
    responses={
        422: {
            "description": "Ошибка валидации — неверный формат или значения полей",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "too_short",
                                "loc": ["body", "title"],
                                "msg": "Строка содержит менее 3 символов",
                                "input": "ab",
                                "ctx": {"limit_value": 3},
                            }
                        ]
                    }
                }
            },
        }
    },
)
def create_task(task: TaskCreate) -> TaskResponse:
    global current_id
    current_id += 1
    new_task = {
        "id": current_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
    }
    tasks_store[current_id] = new_task
    return TaskResponse(**new_task)


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить задачу по ID",
    description="Находит и возвращает задачу по её числовому идентификатору. Если задача не найдена, возвращает ошибку 404.",
    response_description="Данные найденной задачи",
    responses={
        404: {
            "description": "Задача не найдена",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            },
        },
        422: {
            "description": "Ошибка валидации — task_id должен быть числом >= 1",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "greater_than_equal",
                                "loc": ["path", "task_id"],
                                "msg": "Операция сравнения не удалась",
                                "input": "0",
                                "ctx": {"ge": 1},
                            }
                        ]
                    }
                }
            },
        },
    },
)
def get_task(
    task_id: int = Path(
        ...,
        ge=1,
        description="Уникальный целочисленный  ID задачи",
        examples=[1],
    )
) -> TaskResponse:
    task = tasks_store.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return TaskResponse(**task)