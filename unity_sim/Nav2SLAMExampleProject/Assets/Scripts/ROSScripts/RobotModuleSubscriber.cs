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
    public GameObject moduleObject;
}

public class RobotModuleSubscriber : MonoBehaviour
{
    [Header("ROS")]
    [SerializeField] private string moduleChangeTopic = "/robot/module_change";

    [Header("Module State")]
    [SerializeField] private ModuleType currentModule = ModuleType.None;

    [Header("Visual")]
    [SerializeField] private List<ModuleVisualData> moduleVisualList = new List<ModuleVisualData>();

    [Header("Change Effect")]
    [SerializeField] private float changeDelay = 1.0f;
    [SerializeField] private GameObject changingEffectObject;

    private ROSConnection ros;
    private Dictionary<ModuleType, GameObject> moduleVisualMap = new Dictionary<ModuleType, GameObject>();

    private bool isChanging = false;
    private Coroutine changeCoroutine;

    private void Awake()
    {
        foreach (var data in moduleVisualList)
        {
            if (data.moduleObject == null) continue;

            if (!moduleVisualMap.ContainsKey(data.moduleType))
                moduleVisualMap.Add(data.moduleType, data.moduleObject);
        }
    }

    private void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<StringMsg>(moduleChangeTopic, OnReceiveModuleChange);

        ApplyModuleVisual(currentModule);

        if (changingEffectObject != null)
            changingEffectObject.SetActive(false);

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

        Debug.Log($"[Module] 모듈 교체 시작: {currentModule} -> {newModule}");

        if (changingEffectObject != null)
            changingEffectObject.SetActive(true);

        // 필요하면 여기서 현재 모듈 잠깐 끄기
        HideAllModules();

        yield return new WaitForSeconds(changeDelay);

        currentModule = newModule;
        ApplyModuleVisual(currentModule);

        if (changingEffectObject != null)
            changingEffectObject.SetActive(false);

        UpdateModuleUI(currentModule);

        Debug.Log($"[Module] 모듈 교체 완료: {currentModule}");

        isChanging = false;
        changeCoroutine = null;
    }

    private void ApplyModuleVisual(ModuleType module)
    {
        HideAllModules();

        if (moduleVisualMap.TryGetValue(module, out GameObject targetObject))
        {
            targetObject.SetActive(true);
        }
    }

    private void HideAllModules()
    {
        foreach (var pair in moduleVisualMap)
        {
            if (pair.Value != null)
                pair.Value.SetActive(false);
        }
    }

    private void UpdateModuleUI(ModuleType module)
    {
        // 나중에 UI 연결
        // 예: TMP_Text.text = module.ToString();
    }
}