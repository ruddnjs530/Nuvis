using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public enum ModuleType
{
    None,
    Air,
    Dehumid
}

[System.Serializable]
public class ModuleVisualData
{
    public ModuleType moduleType;
    public GameObject equippedObject;   // 로봇에 최종 장착되어 보이는 오브젝트
    public GameObject movingBoxPrefab;  // 스테이션에서 나와 이동하는 프리팹
}

public class RobotModuleSubscriber : MonoBehaviour
{
    [Header("ROS")]
    [SerializeField] 
    private string moduleChangeTopic = "/robot/module_change";

    [Header("Module State")]
    [SerializeField] 
    private ModuleType currentModule = ModuleType.None;

    [Header("Module Visual")]
    [SerializeField] 
    private List<ModuleVisualData> moduleVisualList = new List<ModuleVisualData>();

    [Header("Transfer Points")]
    [SerializeField] 
    private Transform stationSpawnPoint;
    [SerializeField] 
    private Transform robotAttachPoint;

    [Header("Animation")]
    [SerializeField] private float removeDuration = 0.35f;
    [SerializeField] private float removeDropDistance = 0.3f;
    [SerializeField] private float moveDuration = 1.0f;
    [SerializeField] private float moveArcHeight = 0.3f;
    [SerializeField] private float startDelayAfterRemove = 0.1f;

    private ROSConnection ros;
    private Dictionary<ModuleType, ModuleVisualData> moduleVisualMap = new Dictionary<ModuleType, ModuleVisualData>();

    private bool isChanging = false;
    private Coroutine changeCoroutine;

    private void Awake()
    {
        foreach (var data in moduleVisualList)
        {
            if (!moduleVisualMap.ContainsKey(data.moduleType))
            {
                moduleVisualMap.Add(data.moduleType, data);
            }
        }
    }

    private void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<StringMsg>(moduleChangeTopic, OnReceiveModuleChange);

        ApplyEquippedVisual(currentModule);
        Debug.Log($"[Module] 초기 모듈 상태: {currentModule}");
    }

    private void Update()
    {
        // 테스트용
        if (Input.GetKeyDown(KeyCode.Alpha1))
            RequestModuleChange(ModuleType.Air);

        if (Input.GetKeyDown(KeyCode.Alpha2))
            RequestModuleChange(ModuleType.Dehumid);

        if (Input.GetKeyDown(KeyCode.Alpha0))
            RequestModuleChange(ModuleType.None);
    }

    private void OnReceiveModuleChange(StringMsg msg)
    {
        string raw = msg.data.Trim().ToLower();
        Debug.Log($"[Module] 수신한 메시지: {raw}");

        ModuleType newModule = ParseModuleType(raw);
        if (newModule == ModuleType.None)
        {
            Debug.LogWarning($"[Module] 알 수 없는 모듈 값: {raw}");
            return;
        }

        RequestModuleChange(newModule);
    }

    private ModuleType ParseModuleType(string value)
    {
        switch (value)
        {
            case "air": return ModuleType.Air;
            case "dehumid": return ModuleType.Dehumid;
            default: return ModuleType.None;
        }
    }

    private void RequestModuleChange(ModuleType newModule)
    {
        if (isChanging)
        {
            Debug.Log("[Module] 현재 교체 중입니다.");
            return;
        }

        if (currentModule == newModule)
        {
            Debug.Log($"[Module] 이미 {newModule} 모듈입니다.");
            return;
        }

        if (changeCoroutine != null)
            StopCoroutine(changeCoroutine);

        changeCoroutine = StartCoroutine(ChangeModuleRoutine(newModule));
    }

    private IEnumerator ChangeModuleRoutine(ModuleType newModule)
    {
        isChanging = true;

        if (stationSpawnPoint == null || robotAttachPoint == null)
        {
            Debug.LogWarning("[Module] stationSpawnPoint 또는 robotAttachPoint가 비어 있습니다. 바로 교체합니다.");
            currentModule = newModule;
            ApplyEquippedVisual(currentModule);
            isChanging = false;
            changeCoroutine = null;
            yield break;
        }

        if (!moduleVisualMap.TryGetValue(newModule, out ModuleVisualData targetData))
        {
            Debug.LogWarning($"[Module] {newModule}에 해당하는 시각 데이터가 없습니다.");
            isChanging = false;
            changeCoroutine = null;
            yield break;
        }

        Debug.Log($"[Module] 모듈 교체 시작: {currentModule} -> {newModule}");

        // 1. 기존 장착 모듈 제거 연출
        if (currentModule != ModuleType.None && moduleVisualMap.TryGetValue(currentModule, out ModuleVisualData currentData))
        {
            if (currentData.equippedObject != null && currentData.equippedObject.activeSelf)
            {
                yield return StartCoroutine(AnimateRemoveCurrentModule(currentData.equippedObject));
            }
        }

        if (startDelayAfterRemove > 0f)
            yield return new WaitForSeconds(startDelayAfterRemove);

        // 2. 새 박스 생성
        GameObject movingBox = null;
        if (targetData.movingBoxPrefab != null)
        {
            movingBox = Instantiate(
                targetData.movingBoxPrefab,
                stationSpawnPoint.position,
                stationSpawnPoint.rotation);

            movingBox.SetActive(true);
        }

        // 3. 새 박스가 스테이션에서 로봇으로 이동
        float elapsed = 0f;
        Vector3 startPos = stationSpawnPoint.position;
        Vector3 endPos = robotAttachPoint.position;
        Quaternion startRot = stationSpawnPoint.rotation;
        Quaternion endRot = robotAttachPoint.rotation;

        while (elapsed < moveDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / moveDuration);

            if (movingBox != null)
            {
                Vector3 pos = Vector3.Lerp(startPos, endPos, t);
                pos.y += Mathf.Sin(t * Mathf.PI) * moveArcHeight;

                movingBox.transform.position = pos;
                movingBox.transform.rotation = Quaternion.Slerp(startRot, endRot, t);
            }

            yield return null;
        }

        // 4. 이동 박스 제거
        if (movingBox != null)
            Destroy(movingBox);

        // 5. 새 모듈 장착
        currentModule = newModule;
        ApplyEquippedVisual(currentModule);

        Debug.Log($"[Module] 모듈 교체 완료: {currentModule}");

        isChanging = false;
        changeCoroutine = null;
    }

    private IEnumerator AnimateRemoveCurrentModule(GameObject equippedObject)
    {
        Transform tr = equippedObject.transform;
        Vector3 originalLocalPos = tr.localPosition;
        Vector3 targetLocalPos = originalLocalPos + Vector3.down * removeDropDistance;

        float elapsed = 0f;

        while (elapsed < removeDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / removeDuration);

            tr.localPosition = Vector3.Lerp(originalLocalPos, targetLocalPos, t);

            yield return null;
        }

        equippedObject.SetActive(false);
        tr.localPosition = originalLocalPos;
    }

    private void ApplyEquippedVisual(ModuleType module)
    {
        HideAllEquippedModules();

        if (moduleVisualMap.TryGetValue(module, out ModuleVisualData targetData))
        {
            if (targetData.equippedObject != null)
                targetData.equippedObject.SetActive(true);
        }
    }

    private void HideAllEquippedModules()
    {
        foreach (var data in moduleVisualList)
        {
            if (data.equippedObject != null)
                data.equippedObject.SetActive(false);
        }
    }
}