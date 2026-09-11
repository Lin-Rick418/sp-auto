
System.Void PlayerController::ClickSkill(System.Int32) RVA=0xac14f0
00ac14f0 mov      qword ptr [rsp + 8], rbx                      
00ac14f5 mov      qword ptr [rsp + 0x10], rsi                   
00ac14fa push     rdi                                           
00ac14fb sub      rsp, 0x20                                     
00ac14ff xor      r8d, r8d                                      
00ac1502 mov      esi, edx                                      
00ac1504 mov      rbx, rcx                                      
00ac1507 call     0xac3e20                                      SkillState PlayerController::GetAssignedSkill(System.Int32)
00ac150c mov      rdi, rax                                      
00ac150f test     rax, rax                                      
00ac1512 je       0xac156e                                      
00ac1514 xor      edx, edx                                      
00ac1516 mov      rcx, rax                                      
00ac1519 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ac151e test     rax, rax                                      
00ac1521 je       0xac157e                                      
00ac1523 mov      ecx, dword ptr [rax + 0xe4]                   
00ac1529 test     ecx, ecx                                      
00ac152b je       0xac1556                                      
00ac152d cmp      ecx, 3                                        
00ac1530 je       0xac1556                                      
00ac1532 xor      edx, edx                                      
00ac1534 mov      rcx, rdi                                      
00ac1537 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ac153c test     rax, rax                                      
00ac153f je       0xac157e                                      
00ac1541 mov      ecx, dword ptr [rax + 0xe0]                   
00ac1547 cmp      ecx, 1                                        
00ac154a je       0xac1556                                      
00ac154c xor      eax, eax                                      
00ac154e cmp      ecx, 3                                        
00ac1551 sete     al                                            
00ac1554 jmp      0xac155b                                      
00ac1556 mov      eax, 1                                        
00ac155b cmp      byte ptr [rbx + 0x381], 0                     
00ac1562 je       0xac1568                                      
00ac1564 test     eax, eax                                      
00ac1566 je       0xac156e                                      
00ac1568 mov      dword ptr [rbx + 0x454], esi                  
00ac156e mov      rbx, qword ptr [rsp + 0x30]                   
00ac1573 mov      rsi, qword ptr [rsp + 0x38]                   
00ac1578 add      rsp, 0x20                                     
00ac157c pop      rdi                                           
00ac157d ret                                                    
00ac157e call     0x580ca0                                      
00ac1583 int3                                                   
00ac1584 int3                                                   
00ac1585 int3                                                   
00ac1586 int3                                                   
00ac1587 int3                                                   
00ac1588 int3                                                   
00ac1589 int3                                                   
00ac158a int3                                                   
00ac158b int3                                                   
00ac158c int3                                                   
00ac158d int3                                                   
00ac158e int3                                                   
00ac158f int3                                                   

System.Void PlayerController::ProcessTargeting() RVA=0xad3410
00ad3410 mov      qword ptr [rsp + 0x18], rsi                   
00ad3415 mov      qword ptr [rsp + 0x20], rdi                   
00ad341a push     rbp                                           
00ad341b lea      rbp, [rsp - 0x57]                             
00ad3420 sub      rsp, 0xa0                                     
00ad3427 cmp      byte ptr [rip + 0x5699a8f], 0                 
00ad342e mov      rdi, rcx                                      
00ad3431 jne      0xad346a                                      
00ad3433 lea      rcx, [rip + 0x52e400e]                        
00ad343a call     0x5809f0                                      
00ad343f lea      rcx, [rip + 0x52b0b52]                        
00ad3446 call     0x5809f0                                      
00ad344b lea      rcx, [rip + 0x52e3a4e]                        
00ad3452 call     0x5809f0                                      
00ad3457 lea      rcx, [rip + 0x5288be2]                        
00ad345e call     0x5809f0                                      
00ad3463 mov      byte ptr [rip + 0x5699a53], 1                 
00ad346a mov      qword ptr [rsp + 0xb8], rbx                   
00ad3472 xor      esi, esi                                      
00ad3474 movaps   xmmword ptr [rsp + 0x90], xmm6                
00ad347c movaps   xmmword ptr [rsp + 0x80], xmm7                
00ad3484 movaps   xmmword ptr [rsp + 0x70], xmm8                
00ad348a movaps   xmmword ptr [rsp + 0x60], xmm9                
00ad3490 mov      qword ptr [rbp + 0x67], rsi                   
00ad3494 cmp      qword ptr [rdi + 0x438], rsi                  
00ad349b je       0xad3624                                      
00ad34a1 mov      rcx, qword ptr [rdi + 0x138]                  
00ad34a8 test     rcx, rcx                                      
00ad34ab je       0xad3c43                                      
00ad34b1 mov      rdx, qword ptr [rdi + 0x438]                  
00ad34b8 xor      r8d, r8d                                      
00ad34bb call     0x7b86e0                                      System.Boolean SkillsComponent::CanCastStatus(SkillState)
00ad34c0 test     al, al                                        
00ad34c2 je       0xad3624                                      
00ad34c8 mov      rcx, qword ptr [rdi + 0x438]                  
00ad34cf test     rcx, rcx                                      
00ad34d2 je       0xad3c43                                      
00ad34d8 xor      edx, edx                                      
00ad34da call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ad34df test     rax, rax                                      
00ad34e2 je       0xad3c43                                      
00ad34e8 mov      eax, dword ptr [rax + 0xe4]                   
00ad34ee cmp      eax, 1                                        
00ad34f1 jne      0xad3596                                      
00ad34f7 mov      rcx, qword ptr [rdi + 0x438]                  
00ad34fe test     rcx, rcx                                      
00ad3501 je       0xad3c43                                      
00ad3507 xor      edx, edx                                      
00ad3509 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ad350e test     rax, rax                                      
00ad3511 je       0xad3c43                                      
00ad3517 cmp      byte ptr [rax + 0x69], sil                    
00ad351b je       0xad3587                                      
00ad351d movsd    xmm1, qword ptr [rdi + 0x448]                 
00ad3525 xor      eax, eax                                      
00ad3527 movaps   xmm2, xmm1                                    
00ad352a movsd    qword ptr [rbp - 9], xmm1                     
00ad352f movaps   xmm3, xmm1                                    
00ad3532 mov      qword ptr [rbp - 0x19], rax                   
00ad3536 movss    xmm1, dword ptr [rdi + 0x450]                 
00ad353e movd     xmm0, eax                                     
00ad3542 subss    xmm2, xmm0                                    
00ad3546 shufps   xmm3, xmm3, 0x55                              
00ad354a subss    xmm3, dword ptr [rbp - 0x15]                  
00ad354f movd     xmm0, eax                                     
00ad3553 subss    xmm1, xmm0                                    
00ad3557 movss    xmm0, dword ptr [rip + 0x3e3d795]             
00ad355f mulss    xmm3, xmm3                                    
00ad3563 mulss    xmm2, xmm2                                    
00ad3567 mulss    xmm1, xmm1                                    
00ad356b addss    xmm3, xmm2                                    
00ad356f addss    xmm3, xmm1                                    
00ad3573 comiss   xmm0, xmm3                                    
00ad3576 ja       0xad3587                                      
00ad3578 xor      edx, edx                                      
00ad357a mov      rcx, rdi                                      
00ad357d call     0xabf5a0                                      System.Void PlayerController::CastOnGround()
00ad3582 jmp      0xad3624                                      
00ad3587 xor      edx, edx                                      
00ad3589 mov      rcx, rdi                                      
00ad358c call     0xabf740                                      System.Void PlayerController::CastOnTarget()
00ad3591 jmp      0xad3624                                      
00ad3596 cmp      eax, 2                                        
00ad3599 jne      0xad35a7                                      
00ad359b xor      edx, edx                                      
00ad359d mov      rcx, rdi                                      
00ad35a0 call     0xabf5a0                                      System.Void PlayerController::CastOnGround()
00ad35a5 jmp      0xad3624                                      
00ad35a7 mov      rcx, qword ptr [rip + 0x52e3e9a]              
00ad35ae cmp      dword ptr [rcx + 0xe4], esi                   
00ad35b4 jne      0xad35bb                                      
00ad35b6 call     0x580d30                                      
00ad35bb xor      ecx, ecx                                      
00ad35bd call     0x652230                                      System.Boolean App::get_IsServer()
00ad35c2 test     al, al                                        
00ad35c4 jne      0xad35da                                      
00ad35c6 mov      rdx, qword ptr [rdi + 0x438]                  
00ad35cd xor      r8d, r8d                                      
00ad35d0 mov      rcx, rdi                                      
00ad35d3 call     0xac0670                                      System.Void PlayerController::CheckCast_C(SkillState)
00ad35d8 jmp      0xad361a                                      
00ad35da mov      rcx, qword ptr [rdi + 0x138]                  
00ad35e1 xor      eax, eax                                      
00ad35e3 mov      qword ptr [rbp - 0x19], rax                   
00ad35e7 test     rcx, rcx                                      
00ad35ea je       0xad3c43                                      
00ad35f0 movsd    xmm0, qword ptr [rbp - 0x19]                  
00ad35f5 lea      r9, [rbp - 9]                                 
00ad35f9 mov      rdx, qword ptr [rdi + 0x438]                  
00ad3600 xor      r8d, r8d                                      
00ad3603 mov      qword ptr [rsp + 0x28], rsi                   
00ad3608 movsd    qword ptr [rbp - 9], xmm0                     
00ad360d mov      dword ptr [rbp - 1], eax                      
00ad3610 mov      qword ptr [rsp + 0x20], rsi                   
00ad3615 call     0x7b9be0                                      System.Void SkillsComponent::Cast(SkillState,BaseUnitController,UnityEngine.Vector3,IInteractable)
00ad361a xor      edx, edx                                      
00ad361c mov      rcx, rdi                                      
00ad361f call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00ad3624 mov      rax, qword ptr [rdi + 0x130]                  
00ad362b test     rax, rax                                      
00ad362e je       0xad3c43                                      
00ad3634 mov      rcx, qword ptr [rip + 0x5288a05]              
00ad363b mov      rbx, qword ptr [rax + 0x180]                  
00ad3642 cmp      dword ptr [rcx + 0xe4], esi                   
00ad3648 jne      0xad364f                                      
00ad364a call     0x580d30                                      
00ad364f xor      edx, edx                                      
00ad3651 mov      rcx, rbx                                      
00ad3654 call     0x443daf0                                     
00ad3659 test     al, al                                        
00ad365b jne      0xad369d                                      
00ad365d mov      rcx, qword ptr [rip + 0x52889dc]              
00ad3664 mov      rbx, qword ptr [rdi + 0x418]                  
00ad366b cmp      dword ptr [rcx + 0xe4], esi                   
00ad3671 jne      0xad3678                                      
00ad3673 call     0x580d30                                      
00ad3678 xor      edx, edx                                      
00ad367a mov      rcx, rbx                                      
00ad367d call     0x443daf0                                     
00ad3682 test     al, al                                        
00ad3684 je       0xad369d                                      
00ad3686 mov      rcx, qword ptr [rdi + 0x120]                  
00ad368d test     rcx, rcx                                      
00ad3690 je       0xad3c43                                      
00ad3696 xor      edx, edx                                      
00ad3698 call     0x70a390                                      System.Void MoveComponent::Stop()
00ad369d mov      rdx, qword ptr [rdi + 0x130]                  
00ad36a4 test     rdx, rdx                                      
00ad36a7 je       0xad3c43                                      
00ad36ad mov      rdx, qword ptr [rdx + 0x180]                  
00ad36b4 lea      rcx, [rdi + 0x418]                            
00ad36bb mov      qword ptr [rdi + 0x418], rdx                  
00ad36c2 call     0x57fd40                                      
00ad36c7 mov      rax, qword ptr [rdi + 0x130]                  
00ad36ce test     rax, rax                                      
00ad36d1 je       0xad3c43                                      
00ad36d7 mov      rcx, qword ptr [rip + 0x5288962]              
00ad36de mov      rbx, qword ptr [rax + 0x180]                  
00ad36e5 cmp      dword ptr [rcx + 0xe4], esi                   
00ad36eb jne      0xad36f2                                      
00ad36ed call     0x580d30                                      
00ad36f2 xor      edx, edx                                      
00ad36f4 mov      rcx, rbx                                      
00ad36f7 call     0x443daf0                                     
00ad36fc test     al, al                                        
00ad36fe je       0xad37ea                                      
00ad3704 mov      rcx, qword ptr [rdi + 0x130]                  
00ad370b test     rcx, rcx                                      
00ad370e je       0xad3c43                                      
00ad3714 xor      edx, edx                                      
00ad3716 call     0x84d870                                      System.Boolean CombatComponent::get_CanAttack()
00ad371b test     al, al                                        
00ad371d je       0xad37ea                                      
00ad3723 mov      rcx, qword ptr [rip + 0x52b086e]              
00ad372a cmp      dword ptr [rcx + 0xe4], esi                   
00ad3730 jne      0xad3737                                      
00ad3732 call     0x580d30                                      
00ad3737 xor      r8d, r8d                                      
00ad373a xor      edx, edx                                      
00ad373c mov      rcx, rdi                                      
00ad373f call     0xa3f4e0                                      System.Single Formula::AttackRange(BaseUnitController,StatArray)
00ad3744 mov      rdx, qword ptr [rdi + 0x130]                  
00ad374b test     rdx, rdx                                      
00ad374e je       0xad3c43                                      
00ad3754 mov      rdx, qword ptr [rdx + 0x180]                  
00ad375b xor      r9d, r9d                                      
00ad375e mov      rcx, qword ptr [rdi + 0x130]                  
00ad3765 movaps   xmm2, xmm0                                    
00ad3768 mov      qword ptr [rsp + 0x20], rsi                   
00ad376d call     0x84c650                                      System.Boolean CombatComponent::MoveToTarget(BaseUnitController,System.Single,System.Boolean)
00ad3772 mov      rcx, qword ptr [rip + 0x52e3ccf]              
00ad3779 cmp      dword ptr [rcx + 0xe4], esi                   
00ad377f jne      0xad3786                                      
00ad3781 call     0x580d30                                      
00ad3786 xor      ecx, ecx                                      
00ad3788 call     0x652230                                      System.Boolean App::get_IsServer()
00ad378d test     al, al                                        
00ad378f je       0xad37b1                                      
00ad3791 mov      rcx, qword ptr [rdi + 0x130]                  
00ad3798 test     rcx, rcx                                      
00ad379b je       0xad3c43                                      
00ad37a1 movss    xmm1, dword ptr [rip + 0x3e3d4cf]             
00ad37a9 xor      r8d, r8d                                      
00ad37ac call     0x84a290                                      System.Void CombatComponent::Attack(System.Single)
00ad37b1 movaps   xmm9, xmmword ptr [rsp + 0x60]                
00ad37b7 lea      r11, [rsp + 0xa0]                             
00ad37bf mov      rsi, qword ptr [r11 + 0x20]                   
00ad37c3 mov      rdi, qword ptr [r11 + 0x28]                   
00ad37c7 movaps   xmm8, xmmword ptr [rsp + 0x70]                
00ad37cd movaps   xmm7, xmmword ptr [rsp + 0x80]                
00ad37d5 movaps   xmm6, xmmword ptr [rsp + 0x90]                
00ad37dd mov      rbx, qword ptr [rsp + 0xb8]                   
00ad37e5 mov      rsp, r11                                      
00ad37e8 pop      rbp                                           
00ad37e9 ret                                                    
00ad37ea cmp      qword ptr [rdi + 0x410], rsi                  
00ad37f1 je       0xad37b1                                      
00ad37f3 mov      rcx, qword ptr [rip + 0x5288846]              
00ad37fa mov      rbx, qword ptr [rdi + 0x410]                  
00ad3801 cmp      dword ptr [rcx + 0xe4], esi                   
00ad3807 jne      0xad3815                                      
00ad3809 call     0x580d30                                      
00ad380e mov      rcx, qword ptr [rip + 0x528882b]              
00ad3815 mov      r8, qword ptr [rbx]                           
00ad3818 movzx    eax, byte ptr [rcx + 0x130]                   
00ad381f cmp      byte ptr [r8 + 0x130], al                     
00ad3826 jb       0xad3c49                                      
00ad382c movzx    edx, al                                       
00ad382f mov      rax, qword ptr [r8 + 0xc8]                    
00ad3836 cmp      qword ptr [rax + rdx*8 - 8], rcx              
00ad383b jne      0xad3c49                                      
00ad3841 xor      edx, edx                                      
00ad3843 mov      rcx, rbx                                      
00ad3846 call     0x443daf0                                     
00ad384b test     al, al                                        
00ad384d je       0xad37b1                                      
00ad3853 mov      r8, qword ptr [rdi + 0x410]                   
00ad385a test     r8, r8                                        
00ad385d je       0xad3c43                                      
00ad3863 mov      rdx, qword ptr [rip + 0x52e3636]              
00ad386a mov      ecx, 2                                        
00ad386f call     0x30d0                                        
00ad3874 mov      rcx, qword ptr [rip + 0x52887c5]              
00ad387b mov      rbx, rax                                      
00ad387e cmp      dword ptr [rcx + 0xe4], esi                   
00ad3884 jne      0xad388b                                      
00ad3886 call     0x580d30                                      
00ad388b xor      r8d, r8d                                      
00ad388e xor      edx, edx                                      
00ad3890 mov      rcx, rbx                                      
00ad3893 call     0x443db80                                     
00ad3898 test     al, al                                        
00ad389a je       0xad37b1                                      
00ad38a0 mov      r8, qword ptr [rdi + 0x410]                   
00ad38a7 test     r8, r8                                        
00ad38aa je       0xad3c43                                      
00ad38b0 mov      rdx, qword ptr [rip + 0x52e35e9]              
00ad38b7 mov      ecx, 2                                        
00ad38bc call     0x30d0                                        
00ad38c1 test     rax, rax                                      
00ad38c4 je       0xad3c43                                      
00ad38ca xor      edx, edx                                      
00ad38cc mov      rcx, rax                                      
00ad38cf call     0x4426a10                                     
00ad38d4 test     rax, rax                                      
00ad38d7 je       0xad3c43                                      
00ad38dd xor      r8d, r8d                                      
00ad38e0 lea      rcx, [rbp - 9]                                
00ad38e4 mov      rdx, rax                                      
00ad38e7 call     0x44533a0                                     
00ad38ec xor      r8d, r8d                                      
00ad38ef lea      rcx, [rbp + 7]                                
00ad38f3 mov      rdx, rdi                                      
00ad38f6 movsd    xmm7, qword ptr [rax]                         
00ad38fa mov      ebx, dword ptr [rax + 8]                      
00ad38fd call     0x6f00c0                                      UnityEngine.Vector3 BaseUnitController::get_Position()
00ad3902 movsd    qword ptr [rbp - 9], xmm7                     
00ad3907 movaps   xmm3, xmm7                                    
00ad390a movss    xmm8, dword ptr [rbp - 5]                     
00ad3910 movd     xmm9, ebx                                     
00ad3915 movaps   xmm2, xmm8                                    
00ad3919 movsd    xmm1, qword ptr [rax]                         
00ad391d movaps   xmm0, xmm1                                    
00ad3920 movsd    qword ptr [rbp - 9], xmm1                     
00ad3925 subss    xmm3, xmm1                                    
00ad3929 shufps   xmm0, xmm0, 0x55                              
00ad392d movaps   xmm1, xmm9                                    
00ad3931 subss    xmm2, xmm0                                    
00ad3935 subss    xmm1, dword ptr [rax + 8]                     
00ad393a mov      r8, qword ptr [rdi + 0x410]                   
00ad3941 unpcklps xmm3, xmm2                                    
00ad3944 movss    dword ptr [rbp - 1], xmm1                     
00ad3949 movsd    qword ptr [rbp - 9], xmm3                     
00ad394e test     r8, r8                                        
00ad3951 je       0xad3c43                                      
00ad3957 mov      rdx, qword ptr [rip + 0x52e3542]              
00ad395e mov      ecx, 1                                        
00ad3963 call     0x169f0                                       
00ad3968 mov      rcx, qword ptr [rip + 0x52e3ad9]              
00ad396f movaps   xmm6, xmm0                                    
00ad3972 mulss    xmm6, dword ptr [rip + 0x3e3d3b2]             
00ad397a cmp      dword ptr [rcx + 0xe4], esi                   
00ad3980 jne      0xad3987                                      
00ad3982 call     0x580d30                                      
00ad3987 xor      ecx, ecx                                      
00ad3989 call     0x652230                                      System.Boolean App::get_IsServer()
00ad398e mov      rbx, qword ptr [rdi + 0x120]                  
00ad3995 xor      r8d, r8d                                      
00ad3998 lea      rdx, [rbp - 9]                                
00ad399c lea      rcx, [rbp + 7]                                
00ad39a0 test     al, al                                        
00ad39a2 je       0xad3b86                                      
00ad39a8 call     0x6c76b0                                      
00ad39ad movsd    xmm1, qword ptr [rax]                         
00ad39b1 subss    xmm9, dword ptr [rax + 8]                     
00ad39b7 movaps   xmm0, xmm1                                    
00ad39ba movsd    qword ptr [rbp - 9], xmm1                     
00ad39bf shufps   xmm0, xmm0, 0x55                              
00ad39c3 subss    xmm7, xmm1                                    
00ad39c7 subss    xmm8, xmm0                                    
00ad39cc mov      r8, qword ptr [rdi + 0x410]                   
00ad39d3 test     r8, r8                                        
00ad39d6 je       0xad3c43                                      
00ad39dc mov      rdx, qword ptr [rip + 0x52e34bd]              
00ad39e3 mov      ecx, 3                                        
00ad39e8 call     0x30d0                                        
00ad39ed test     rbx, rbx                                      
00ad39f0 je       0xad3c43                                      
00ad39f6 unpcklps xmm7, xmm8                                    
00ad39fa lea      rdx, [rbp - 9]                                
00ad39fe movzx    r9d, al                                       
00ad3a02 movsd    qword ptr [rbp - 9], xmm7                     
00ad3a07 movaps   xmm2, xmm6                                    
00ad3a0a movss    dword ptr [rbp - 1], xmm9                     
00ad3a10 mov      rcx, rbx                                      
00ad3a13 mov      qword ptr [rsp + 0x20], rsi                   
00ad3a18 call     0x7091e0                                      System.Boolean MoveComponent::MoveToRange(UnityEngine.Vector3,System.Single,System.Boolean)
00ad3a1d test     al, al                                        
00ad3a1f je       0xad37b1                                      
00ad3a25 cmp      byte ptr [rip + 0x5699488], sil               
00ad3a2c mov      rbx, qword ptr [rdi + 0x410]                  
00ad3a33 jne      0xad3a54                                      
00ad3a35 lea      rcx, [rip + 0x52a3c74]                        
00ad3a3c call     0x5809f0                                      
00ad3a41 lea      rcx, [rip + 0x52e3458]                        
00ad3a48 call     0x5809f0                                      
00ad3a4d mov      byte ptr [rip + 0x5699460], 1                 
00ad3a54 cmp      qword ptr [rdi + 0x438], rsi                  
00ad3a5b je       0xad3b39                                      
00ad3a61 test     rbx, rbx                                      
00ad3a64 je       0xad3b39                                      
00ad3a6a mov      rcx, qword ptr [rdi + 0x438]                  
00ad3a71 xor      edx, edx                                      
00ad3a73 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ad3a78 test     rax, rax                                      
00ad3a7b je       0xad3c43                                      
00ad3a81 cmp      dword ptr [rax + 0xe0], 7                     
00ad3a88 jne      0xad3b39                                      
00ad3a8e mov      rdx, qword ptr [rip + 0x52e340b]              
00ad3a95 mov      ecx, 2                                        
00ad3a9a mov      r8, rbx                                       
00ad3a9d call     0x30d0                                        
00ad3aa2 test     rax, rax                                      
00ad3aa5 je       0xad3c43                                      
00ad3aab mov      r8, qword ptr [rip + 0x52a3bfe]               
00ad3ab2 lea      rdx, [rbp + 0x67]                             
00ad3ab6 mov      rcx, rax                                      
00ad3ab9 call     0xfb2ea0                                      
00ad3abe test     al, al                                        
00ad3ac0 je       0xad3b39                                      
00ad3ac2 mov      rcx, qword ptr [rdi + 0x138]                  
00ad3ac9 test     rcx, rcx                                      
00ad3acc je       0xad3c43                                      
00ad3ad2 mov      rdx, qword ptr [rdi + 0x438]                  
00ad3ad9 xor      r8d, r8d                                      
00ad3adc call     0x7b8940                                      System.Boolean SkillsComponent::CanCast(SkillState)
00ad3ae1 test     al, al                                        
00ad3ae3 je       0xad37b1                                      
00ad3ae9 mov      rcx, qword ptr [rdi + 0x138]                  
00ad3af0 xor      eax, eax                                      
00ad3af2 mov      qword ptr [rbp - 0x19], rax                   
00ad3af6 test     rcx, rcx                                      
00ad3af9 je       0xad3c43                                      
00ad3aff movsd    xmm0, qword ptr [rbp - 0x19]                  
00ad3b04 lea      r9, [rbp - 9]                                 
00ad3b08 mov      rdx, qword ptr [rdi + 0x438]                  
00ad3b0f xor      r8d, r8d                                      
00ad3b12 mov      dword ptr [rbp - 1], eax                      
00ad3b15 mov      rax, qword ptr [rbp + 0x67]                   
00ad3b19 mov      qword ptr [rsp + 0x28], rsi                   
00ad3b1e mov      qword ptr [rsp + 0x20], rax                   
00ad3b23 movsd    qword ptr [rbp - 9], xmm0                     
00ad3b28 call     0x7b9be0                                      System.Void SkillsComponent::Cast(SkillState,BaseUnitController,UnityEngine.Vector3,IInteractable)
00ad3b2d xor      edx, edx                                      
00ad3b2f mov      rcx, rdi                                      
00ad3b32 call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00ad3b37 jmp      0xad3b6c                                      
00ad3b39 xor      edx, edx                                      
00ad3b3b mov      qword ptr [rbp + 0x67], rsi                   
00ad3b3f lea      rcx, [rbp + 0x67]                             
00ad3b43 call     0x57fd40                                      
00ad3b48 mov      r8, qword ptr [rdi + 0x410]                   
00ad3b4f test     r8, r8                                        
00ad3b52 je       0xad3c43                                      
00ad3b58 mov      rdx, qword ptr [rip + 0x52e3341]              
00ad3b5f mov      ecx, 5                                        
00ad3b64 mov      r9, rdi                                       
00ad3b67 call     0x103a0                                       
00ad3b6c lea      rcx, [rdi + 0x410]                            
00ad3b73 mov      qword ptr [rdi + 0x410], rsi                  
00ad3b7a xor      edx, edx                                      
00ad3b7c call     0x57fd40                                      
00ad3b81 jmp      0xad37b1                                      
00ad3b86 call     0x6c76b0                                      
00ad3b8b movsd    xmm1, qword ptr [rax]                         
00ad3b8f subss    xmm9, dword ptr [rax + 8]                     
00ad3b95 movaps   xmm0, xmm1                                    
00ad3b98 movsd    qword ptr [rbp - 9], xmm1                     
00ad3b9d shufps   xmm0, xmm0, 0x55                              
00ad3ba1 subss    xmm7, xmm1                                    
00ad3ba5 subss    xmm8, xmm0                                    
00ad3baa mov      r8, qword ptr [rdi + 0x410]                   
00ad3bb1 test     r8, r8                                        
00ad3bb4 je       0xad3c43                                      
00ad3bba mov      rdx, qword ptr [rip + 0x52e32df]              
00ad3bc1 mov      ecx, 3                                        
00ad3bc6 call     0x30d0                                        
00ad3bcb test     rbx, rbx                                      
00ad3bce je       0xad3c43                                      
00ad3bd0 unpcklps xmm7, xmm8                                    
00ad3bd4 lea      rdx, [rbp - 9]                                
00ad3bd8 movzx    r9d, al                                       
00ad3bdc movsd    qword ptr [rbp - 9], xmm7                     
00ad3be1 movaps   xmm2, xmm6                                    
00ad3be4 movss    dword ptr [rbp - 1], xmm9                     
00ad3bea mov      rcx, rbx                                      
00ad3bed mov      qword ptr [rsp + 0x20], rsi                   
00ad3bf2 call     0x7091e0                                      System.Boolean MoveComponent::MoveToRange(UnityEngine.Vector3,System.Single,System.Boolean)
00ad3bf7 test     al, al                                        
00ad3bf9 je       0xad37b1                                      
00ad3bff mov      r8, qword ptr [rdi + 0x410]                   
00ad3c06 test     r8, r8                                        
00ad3c09 je       0xad3c43                                      
00ad3c0b mov      rdx, qword ptr [rip + 0x52e328e]              
00ad3c12 mov      ecx, 5                                        
00ad3c17 mov      r9, rdi                                       
00ad3c1a call     0x103a0                                       
00ad3c1f lea      rcx, [rdi + 0x410]                            
00ad3c26 mov      qword ptr [rdi + 0x410], rsi                  
00ad3c2d xor      edx, edx                                      
00ad3c2f call     0x57fd40                                      
00ad3c34 xor      edx, edx                                      
00ad3c36 mov      rcx, rdi                                      
00ad3c39 call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00ad3c3e jmp      0xad37b1                                      
00ad3c43 call     0x580ca0                                      
00ad3c48 int3                                                   
00ad3c49 mov      rdx, rcx                                      
00ad3c4c mov      rcx, rbx                                      
00ad3c4f call     0x57fd80                                      
00ad3c54 int3                                                   
00ad3c55 int3                                                   
00ad3c56 int3                                                   
00ad3c57 int3                                                   
00ad3c58 int3                                                   
00ad3c59 int3                                                   
00ad3c5a int3                                                   
00ad3c5b int3                                                   
00ad3c5c int3                                                   
00ad3c5d int3                                                   
00ad3c5e int3                                                   
00ad3c5f int3                                                   
